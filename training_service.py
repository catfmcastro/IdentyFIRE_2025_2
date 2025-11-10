import logging
import os
import subprocess
import uuid
from concurrent import futures

import grpc
import identyfire_pb2
import identyfire_pb2_grpc


class TrainingServicer(identyfire_pb2_grpc.TrainingServiceServicer):
    def __init__(self):
        self.jobs = {}
        logging.info("TrainingServicer initialized")

    def SubmitTrainingJob(self, request, context):
        """Submit a training job. Launches a subprocess running main.py."""
        job_id = str(uuid.uuid4())[:8]
        output_dir = os.path.join("models", job_id)
        os.makedirs(output_dir, exist_ok=True)

        log_path = os.path.join(output_dir, "train.log")

        cmd = [
            "python",
            "main.py",
            "--dataset",
            request.dataset_uri,
            "--epochs",
            str(request.epochs),
            "--output-dir",
            output_dir,
        ]

        try:
            stdout_log = open(log_path, "w")
            stderr_log = open(log_path + ".err", "w")
            proc = subprocess.Popen(cmd, stdout=stdout_log, stderr=stderr_log)
            self.jobs[job_id] = {
                "process": proc,
                "status": "RUNNING",
                "log_path": log_path,
                "output_dir": output_dir,
            }
            logging.info(f"Job {job_id} submitted with PID {proc.pid}")
            return identyfire_pb2.JobResponse(job_id=job_id)
        except Exception as e:
            logging.exception(f"Error submitting job {job_id}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error submitting job: {e}")
            return identyfire_pb2.JobResponse()

    def GetJobStatus(self, request, context):
        """Get the status of a training job."""
        job_id = request.job_id

        if job_id not in self.jobs:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Job {job_id} not found")
            return identyfire_pb2.JobStatusResponse()

        job_info = self.jobs[job_id]
        proc = job_info["process"]
        log_path = job_info["log_path"]

        status_code = proc.poll()

        if status_code is None:
            state = identyfire_pb2.JobStatusResponse.State.RUNNING
        elif status_code == 0:
            state = identyfire_pb2.JobStatusResponse.State.COMPLETED
        else:
            state = identyfire_pb2.JobStatusResponse.State.FAILED

        logging.info(f"Job {job_id} status: {state}")
        return identyfire_pb2.JobStatusResponse(state=state, logs_path=log_path)


def serve(host="localhost", port=50052):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    identyfire_pb2_grpc.add_TrainingServiceServicer_to_server(TrainingServicer(), server)
    bind_addr = f"{host}:{port}"
    server.add_insecure_port(bind_addr)
    server.start()
    logging.info(f"Training service gRPC rodando em {bind_addr}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutdown solicitado por teclado. Parando o servidor...")
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
