from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from adsputils import setup_logging
import json

def exec_commands(api_instance, name, namespace, identifier, logger):
    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=name,
                                                namespace=namespace)
    except ApiException as e:
        if e.status != 404:
            logger.error(f"Unknown error: {e}")
            raise(e)


    # Calling exec and waiting for response
    exec_command = ["/bin/bash", "-c", "curl -w 'formatted string' --silent --url 'http://localhost:9983/solr/collection1/select?fl=identifier&q=identifier%3A{}&wt=json'".format(identifier)] #[
    try:
        resp = stream(api_instance.connect_get_namespaced_pod_exec,
                  name,
                  namespace,
                  command=exec_command,
                  stderr=True, stdin=False,
                  stdout=True, tty=False)      
        test=json.loads(''.join(resp.split('\n')[:-1]))
        if test['response']['numFound'] > 0:
            logger.info("pod: {} has record: {}".format(name, identifier) )
            logger.info("Response: {} from pod: {}".format(json.dumps(test), identifier))
            if test['response']['numFound'] > 1: 
                logger.error("pod: {} returned more than one record for identifier:{}".format(name, identifier) )
            return 1.
        else:
            logger.info("pod: {} does not have record: {}".format(name, identifier) )
            return 0.
    except:
        logger.info("Failed to get response from solr pod")
        return 0.


def check_solr_update_status(ads_config, identifier):
    logger = setup_logging('kube_util.py', proj_home=ads_config.get('PROJ_HOME','..'),
                        level=ads_config.get('LOGGING_LEVEL', 'INFO'),
                        attach_stdout=ads_config.get('LOG_STDOUT', False))
    namespace=ads_config.get("KUBE_ENV", "solr-dev")  
    config.load_kube_config(config_file=ads_config.get("KUBE_CONFIG"))
    try:
        c = Configuration().get_default_copy()
    except AttributeError:
        c = Configuration()
        c.assert_hostname = False
    Configuration.set_default(c)
    core_v1 = core_v1_api.CoreV1Api()

    pod_list = core_v1.list_namespaced_pod(namespace)
    num_updated = 0.
    num_total = 0.
    for pod in pod_list.items:
        if "solr-searcher" in pod.metadata.name: 
            num_updated +=exec_commands(core_v1, pod.metadata.name, namespace, identifier, logger)
            num_total +=1
    
    logger.info(f"{num_updated}/{num_total} searchers updated")
    if num_updated/num_total == 1:
        return True
    else: 
        return False