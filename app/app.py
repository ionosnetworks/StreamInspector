from inspector import StreamInspector, StreamStates
from mysql import MySqlHelper
from dotenv import load_dotenv
import os
import random
import time
from slack import post_status_to_slack
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ignore_orgs = [1,2, 220, 463, 461]

ORGS_TO_INSPECT = os.environ.get("ORGS")
DEFAULT_ACCOUNT_PASSWORD = os.environ.get("DEFAULT_ACCOUNT_PASSWORD")

def get_org_user_details(orgs_to_inspect: str):
    # Try to filter down to single installer account per org
    try:
        orgs_to_inspect = [int(o.strip()) for o in orgs_to_inspect.split(',')]
        orgs_to_inspect_str = ', '.join(map(str, orgs_to_inspect))
        query = f"""
            select
            users.organization_id as org_id,
            organizations.name as org_name,
            email_address
            from
            users
            join organizations on users.organization_id = organizations.organization_id
            where
            users.organization_id in ({orgs_to_inspect_str})
            and email_address like 'lrm_installer%'
        """
        db_runner = MySqlHelper()
        db_runner.connect()
        result = db_runner.execute_query(query)
        db_runner.disconnect()
        if not result:
            logger.info("Empty response: No installer accounts found for org")
            return None
        logger.debug(f"User Accounts Info: {result}")
        return result
    except Exception as e:
        logger.error(f"Could not get User account details: {e}", exc_info=True)
        return None
   

def get_cameras_for_org(org_id: int, db_runner=None):
    try:
        if db_runner is None:
            db_runner = MySqlHelper()
        query = f"""
            select
            substring_index(loc.location_name, ',', 1) as location,
            right(cr.server_id, 4) as server_id,
            group_concat(camera_id) as camera_ids
            from
            cameras_readonly cr
            join locations loc on cr.location_id = loc.location_id
            where
            loc.organization_id = {org_id}
            and (cr.failed is null 
            or (
                cr.failed not like '%timed%'
                and cr.failed not like '%disconnect%'
                and cr.failed not like '%error%'
                and cr.failed not like '%refused%'
            ))
            group by location
        """
        if db_runner.connection is None:
            db_runner.connect()
        result = db_runner.execute_query(query)
        # db_runner.disconnect() # check here <--
        if result:
            for location_dict in result:
                if 'camera_ids' in location_dict:
                    camera_ids_list = location_dict['camera_ids'].split(',')
                    no_of_selections = min(random.randint(2, 3), len(camera_ids_list))
                    selected_cameras = random.sample(camera_ids_list, no_of_selections)
                    location_dict['camera_ids'] = selected_cameras
                else:
                    logger.warning(f"No online cameras found for location : {location_dict}")
            return result
        else:
            logger.warning("No online cameras found. Empty response from query.")
            return None  
    except Exception as e:
        logger.error(f"Could not get camera info : {str(e)}", exc_info=True)
        return None
    

def start_workflow():
    try:
        db_runner = MySqlHelper()
        db_runner.connect()
        stream_states_result = []
        # get Org user accounts
        account_info = get_org_user_details(ORGS_TO_INSPECT)
        if account_info is None:
            db_runner.disconnect()
            logger.warning("Nothing to check. goodbye")
            return None
        else:
            # process each org
            for account in account_info:
                # spawn a browser
                try:
                    inspector = StreamInspector()
                    inspector.login(account["email_address"], DEFAULT_ACCOUNT_PASSWORD)
                except Exception as e:
                    logger.error(f"Web driver error : {str(e)}", exc_info=True)
                    return None
                logger.info(f"Processing ORG : {account['org_name']}")
                # get camera details for the org
                camera_info = get_cameras_for_org(int(account['org_id']), db_runner)
                if camera_info is not None:
                    org_stream_state = {'org_id': int(account['org_id']), 'org_name' : account['org_name'], 'locations' : []}
                    for location_dict in camera_info:
                        location_record = {'location_name': location_dict['location'], 'camera_ids': [], 'stream_states': []}
                        logger.info(f"Processing Location : {location_dict['location']}")
                        for camera_id in location_dict['camera_ids']:
                            logger.info(f"Processing {camera_id} - waiting for few seconds")
                            # get state from camera
                            time.sleep(random.randint(5,15))
                            stream_state = inspector.check_live_stream(camera_id)
                            logger.info(f"{camera_id} state returned as : {stream_state}")
                            location_record['camera_ids'].append(camera_id)
                            location_record['stream_states'].append(stream_state) 
                        org_stream_state['locations'].append(location_record)
                    stream_states_result.append(org_stream_state)
            return stream_states_result
    except Exception as e:
        logger.error(f"Automated workflow interrupted by {e}", exc_info=True)
        return None
    finally:
        if db_runner is not None:
            db_runner.disconnect()
        if inspector is not None:
            inspector.close_driver()

def main():
    inspection_result = start_workflow()
    if inspection_result is not None:
        logger.info(f"Workflow Result : {inspection_result}")
        post_status_to_slack(inspection_result)
    logger.info(f"Execution successfull")

if __name__ == '__main__':
    main()




