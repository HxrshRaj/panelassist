"""
PanelAssist web API.

    uvicorn webapp.backend.app:app --reload        (from the repository root)

Reviews run as short background jobs (a full review makes 7 sequential model
calls and can take over a minute), so the browser polls /api/jobs/{id}.
Every report says where it came from: live, offline_demo or deterministic_only.
"""
import os
import threading
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from webapp.backend import ingest, service
from webapp.backend.db import Store, sha256_text
from webapp.backend.guard import sanitise_submission
from rubric import RUBRIC

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(ROOT, "webapp", "frontend", "dist")
CRITERIA = {c["id"]: c for c in RUBRIC}


class ReviewRequest(BaseModel):
    title: str = Field("", max_length=120)
    readme: str
    reproduce: str = ""
    trajectory: str = ""
    files: str = ""
    mode: str = Field("lean", pattern="^(full|lean)$")
    sample_slug: str | None = Field(None, max_length=80)


class FlagRating(BaseModel):
    check: str = Field(max_length=60)
    useful: bool


class JudgeScore(BaseModel):
    criterion_id: str
    judge_score: int
    note: str = Field("", max_length=2000)


class JudgeReview(BaseModel):
    scores: list[JudgeScore]
    seconds_to_review: float | None = Field(None, ge=0, le=86_400)


def create_app(db_path: str | None = None, max_live_per_day: int | None = None) -> FastAPI:
    app = FastAPI(title="PanelAssist", version="2.0",
                  description="Advisory pre-screening for hackathon judging. Never makes a final decision.")
    origins = [o.strip() for o in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["*"])

    store = Store(db_path or os.environ.get(
        "PANELASSIST_DB", os.path.join(ROOT, "webapp", "data", "panelassist.db")))
    live_cap = max_live_per_day if max_live_per_day is not None else int(os.environ.get("MAX_LIVE_REVIEWS_PER_DAY", "20"))
    jobs: dict = {}
    jobs_lock = threading.Lock()
    hits: dict = defaultdict(deque)
    app.state.store = store

    def rate_limit(request: Request, limit: int = 12, window: int = 60):
        ip = request.client.host if request.client else "unknown"
        q = hits[ip]
        now = time.time()
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, "Too many requests; please wait a minute.")
        q.append(now)

    # -- read-only ---------------------------------------------------------
    @app.get("/api/health")
    def health():
        live = service.llm_configured()
        return {"status": "ok", "llm_configured": live,
                "mode": "live" if live else "offline",
                "message": ("A model is configured; reviews run live." if live else
                            "No model key is configured on this server. You can replay stored real runs of the "
                            "synthetic samples (clearly labelled), and the write-up check still runs.")}

    @app.get("/api/samples")
    def samples():
        return service.list_samples()

    @app.get("/api/samples/{slug}")
    def sample(slug: str):
        s = service.get_sample(slug)
        if not s:
            raise HTTPException(404, "No such sample.")
        return s

    @app.get("/api/stats")
    def stats():
        return store.stats()

    # -- reviewing -----------------------------------------------------------
    def start_job(sub: dict, mode: str, sample_slug: str | None):
        clean, findings = sanitise_submission(sub)
        warnings = [{"kind": f["kind"], "where": f"{f['source']} line {f['line']}", "excerpt": f["excerpt"]}
                    for f in findings]
        title = sub.get("title") or "Untitled submission"
        digest = sha256_text(sub.get("readme", ""), sub.get("reproduce", ""), sub.get("trajectory_raw", ""))
        job_id = uuid.uuid4().hex

        def finish(report):
            review_id = store.create_review(
                report["source"], title, digest, report["advisory_total"],
                [{"check": f["check"], "passed": f["passed"]} for f in report["flags"]],
                {c["id"]: c["advisory_score"] for c in report["criteria"] if c["advisory_score"] is not None})
            report["review_id"] = review_id
            return report

        if service.llm_configured():
            if store.count_live_today() >= live_cap:
                raise HTTPException(429, f"This server allows {live_cap} live reviews per day and has reached "
                                         "the limit. Try an offline sample, or run the CLI yourself.")
            with jobs_lock:
                if sum(1 for j in jobs.values() if j["status"] in ("queued", "running")) >= 3:
                    raise HTTPException(429, "The server is busy with other reviews; try again shortly.")
                jobs[job_id] = {"status": "running", "started": time.time()}

            def work():
                try:
                    review = service.run_pipeline(clean, mode)
                    note = f"LIVE - the {mode} pipeline just ran against the configured model."
                    report = service.report_from_review(review, "live", note, title, warnings)
                    result = {"status": "done", "report": finish(report)}
                except Exception as exc:  # noqa: BLE001 - surface any failure to the judge, honestly
                    result = {"status": "error",
                              "error": f"The model call failed ({type(exc).__name__}: {str(exc)[:200]}). "
                                       "No score was produced."}
                with jobs_lock:
                    jobs[job_id] = {**result, "started": jobs[job_id]["started"]}

            threading.Thread(target=work, daemon=True).start()
            return job_id

        # no model configured: offline replay for a known sample, else deterministic-only
        report = None
        if sample_slug:
            report = service.demo_report(sample_slug, clean.get("readme", ""), warnings)
            if report:
                report["title"] = title
        if report is None:
            report = service.deterministic_report(title, clean.get("readme", ""), warnings)
        with jobs_lock:
            jobs[job_id] = {"status": "done", "report": finish(report), "started": time.time()}
        return job_id

    @app.post("/api/review")
    def review(req: ReviewRequest, request: Request):
        rate_limit(request)
        try:
            sub = ingest.from_text(req.title, req.readme, req.reproduce, req.trajectory, req.files)
        except ingest.InputError as e:
            raise HTTPException(422, str(e))
        return {"job_id": start_job(sub, req.mode, req.sample_slug)}

    @app.post("/api/review/upload")
    async def review_upload(request: Request, file: UploadFile = File(...), title: str = Form(""),
                            mode: str = Form("lean")):
        rate_limit(request)
        if mode not in ("full", "lean"):
            raise HTTPException(422, "mode must be 'full' or 'lean'.")
        data = await file.read(ingest.MAX_ZIP_BYTES + 1)
        try:
            sub = ingest.from_zip(data, title[:120])
        except ingest.InputError as e:
            raise HTTPException(422, str(e))
        return {"job_id": start_job(sub, mode, None)}

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        with jobs_lock:
            j = jobs.get(job_id)
        if not j:
            raise HTTPException(404, "Unknown job.")
        return {k: v for k, v in j.items() if k != "started"} | {"elapsed_seconds": round(time.time() - j["started"], 1)}

    # -- judge feedback ------------------------------------------------------
    @app.post("/api/reviews/{review_id}/flags")
    def rate_flag(review_id: int, body: FlagRating):
        if not store.review_exists(review_id):
            raise HTTPException(404, "Unknown review.")
        store.rate_flag(review_id, body.check, body.useful)
        return {"ok": True}

    @app.post("/api/reviews/{review_id}/judge")
    def judge(review_id: int, body: JudgeReview):
        if not store.review_exists(review_id):
            raise HTTPException(404, "Unknown review.")
        advisory = store.get_advisory(review_id)
        judged = []
        for s in body.scores:
            crit = CRITERIA.get(s.criterion_id)
            if not crit:
                raise HTTPException(422, f"Unknown criterion {s.criterion_id}.")
            if not 0 <= s.judge_score <= crit["points"]:
                raise HTTPException(422, f"{crit['name']} must be between 0 and {crit['points']}.")
            judged.append({"criterion_id": s.criterion_id, "max_points": crit["points"],
                           "advisory_score": advisory.get(s.criterion_id),
                           "judge_score": s.judge_score, "note": s.note})
        if len(judged) != len(CRITERIA) or len({j["criterion_id"] for j in judged}) != len(CRITERIA):
            raise HTTPException(422, "Provide exactly one score for each of the six criteria.")
        total = store.save_judge_review(review_id, judged, body.seconds_to_review)
        return {"ok": True, "judge_total": total}

    if os.path.isdir(FRONTEND_DIST):
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.exception_handler(HTTPException)
    async def http_error(_request, exc: HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return app


app = create_app()
