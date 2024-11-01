from locust import HttpUser,task,between
from locust.stats import global_stats
import random
manifest_ids = ["69429/g05t3fx73x7t"]
class AppUser(HttpUser):
    wait_time = between(2,5)

    def on_start(self) -> None:
        """
        Clear statistics at the start of the test.
        """
        global_stats.reset_all()

    @task
    def get_files(self):
        manifest_id = random.choice(manifest_ids)
        self.client.get("/manifest/" + str(manifest_id))
