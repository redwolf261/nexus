import asyncio
import json
import uuid
import traceback
from sqlalchemy.orm import Session
from backend.db.schema import BackgroundJob
from backend.database import SessionLocal
from backend.core.logging import logger

class JobRunner:
    @staticmethod
    def submit_job(db: Session, task_name: str, payload: dict) -> str:
        job_id = "JOB-" + str(uuid.uuid4())[:8].upper()
        job = BackgroundJob(
            id=job_id,
            task_name=task_name,
            payload=json.dumps(payload),
            state="QUEUED"
        )
        db.add(job)
        db.commit()
        
        # In a real distributed system, a worker would poll or be notified. 
        # Here we just fire off a background task to process it immediately if possible.
        asyncio.create_task(JobRunner.process_job(job_id))
        return job_id

    @staticmethod
    async def process_job(job_id: str):
        db = SessionLocal()
        try:
            # We don't have true lock-wait in sqlite, so we just try to claim it
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if not job or job.state not in ["QUEUED", "RETRYING"]:
                return
                
            job.state = "RUNNING"
            job.attempts += 1
            db.commit()
            
            payload = json.loads(job.payload)
            
            if job.task_name == "process_intelligence_event":
                from backend.workers.intelligence_worker import process_intelligence_event
                from backend.events.event_models import BaseEvent
                event = BaseEvent(**payload)
                await process_intelligence_event(event)
                
            job.state = "SUCCEEDED"
            db.commit()
        except Exception as e:
            db.rollback()
            job = db.query(BackgroundJob).filter_by(id=job_id).first()
            if job:
                job.error_msg = traceback.format_exc()
                if job.attempts >= 3:
                    job.state = "FAILED"
                else:
                    job.state = "RETRYING"
                    # Schedule retry
                    asyncio.create_task(JobRunner.retry_job_later(job_id))
                db.commit()
            logger.error(f"[Worker] Job {job_id} failed: {e}")
        finally:
            db.close()
            
    @staticmethod
    async def retry_job_later(job_id: str):
        await asyncio.sleep(5)
        await JobRunner.process_job(job_id)
