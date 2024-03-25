from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import polling2
from mysql import MySqlHelper
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


ignore_orgs = [1,2, 220, 463, 461]


class StreamStates(Enum):
    CANT_LOAD_CAMERA_PAGE = "CANT_LOAD_CAMERA_PAGE"
    TOO_LONG_TO_LOAD = "TOO_LONG_TO_LOAD"
    LOADED = "LOADED"
    NO_SIGNAL = "NO_SIGNAL"
    INTERNAL_SERVICE_ERROR = "INTERNAL_SERVICE_ERROR"
    LOGIN_ERROR = "LOGIN_ERROR"

class StreamInspector:
    def __init__(self) -> None:
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--incognito")
            options.add_argument("--no-first-run")
            options.add_argument("start-maximized")
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 60)
        except Exception as e:
            logger.error(f"Exception occurred during web driver init:", exc_info=True)
            return StreamStates.INTERNAL_SERVICE_ERROR

    def login(self, email: str, password: str):
        try:
            logger.info(f"trying to login using : {email}")
            self.driver.get("https://app.livereach.ai/login")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            username_input = self.driver.find_element(By.ID, 'username')
            password_input = self.driver.find_element(By.ID, 'password')
            remember_me_input = self.driver.find_element(By.ID, 'isRememberMe')
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            username_input.send_keys(email)
            password_input.send_keys(password)
            remember_me_input.click()
            submit_button.click()
            self.wait.until(EC.url_contains("https://app.livereach.ai/live/overview"))
        except Exception as e:
            logger.error(f"Exception occurred during login:", exc_info=True)
            return StreamStates.LOGIN_ERROR

    def _verify_stream_status(self):
        video_element = self.driver.find_element(By.TAG_NAME, "video")
        video_attr_current_time = video_element.get_property("currentTime")
        video_attr_paused = video_element.get_property("paused")
        video_attr_ended = video_element.get_property("ended")
        video_attr_ready_state = video_element.get_property("readyState")
        logger.info(f"Attributes CT : {video_attr_current_time} PAUSE : {video_attr_paused} ENDED : {video_attr_ended} RS : {video_attr_ready_state}")
        if video_attr_current_time > 1 and not video_attr_paused and video_attr_ready_state > 2:
            return StreamStates.LOADED
        elif "no signal" in self.driver.page_source:
            return StreamStates.NO_SIGNAL
        else:
            return None
    
    def check_live_stream(self, camera_id: str) -> None:
        camera_url = f"https://app.livereach.ai/cameras/{camera_id}"
        self.driver.get(camera_url)

        try:
            WebDriverWait(self.driver, 50).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        except Exception as e:
            logger.error(f"Unable to Load Camera page:", exc_info=True)
            return StreamStates.CANT_LOAD_CAMERA_PAGE
        try:
            poll_result = polling2.poll(lambda: self._verify_stream_status(),
                          check_success=lambda result: result is not None,
                          step=2,
                          timeout=60
                          )
            return poll_result
        except polling2.TimeoutException:
            return StreamStates.TOO_LONG_TO_LOAD
        except Exception as e:
            logger.error(f"Exception occurred during camera video check:", exc_info=True)
            return StreamStates.INTERNAL_SERVICE_ERROR
        
    def close_driver(self):
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Driver closed and memory freed")
        except Exception as e:
            logger.error(f"Exception occurred when closing driver:", exc_info=True)
      





