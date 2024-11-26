import unittest
from unittest.mock import patch, Mock
import os
import httpretty
import pytest
import myadsp.kube_utils as kube_utils
from kubernetes.client.rest import ApiException
from kubernetes.client.models.v1_object_meta import V1ObjectMeta

class MockKubernetes():
    def __init__(self):
        pass

    def list_namespaced_pod(*args, **kwargs):
        class MockPods():
            def __init__(self, *args, **kwargs):
                self.__class__
                self.items = [MockPod(*args, **kwargs)]
        class MockPod():
            def __init__(self, *args, **kwargs):
                self.metadata = metadata(*args, **kwargs)

        class metadata():
            def __init__(self, *args, **kwargs):
                if args[1]=='Success':
                    self.name = "solr-searcher-us-east-1c-0"
                else:
                    self.name = "solr-searcher-us-east-1d-0"
                
        return MockPods(*args, **kwargs)
    class stream():
        def __init__(self, *args, **kwargs):
            self.stream= None

    def read_namespaced_pod(*args, **kwargs):
        class MockPodApI():
            def __init__(self, *args, **kwargs):
                self.status = self.get_status(*args, **kwargs)
            def get_status(self, *args, **kwargs):
                success=kwargs.get("name")
                if success == "solr-searcher-us-east-1c-0": 
                    return 200 
                else:
                    raise ApiException(status=400, reason='test failure')
        return MockPodApI(*args, **kwargs).status
    
    def stream(*args, **kwargs):
        class MockStream():
            def __init__(self, *args, **kwargs):
                self.resp = self.connect_get_namespaced_pod_exec()
            def connect_get_namespaced_pod_exec(*args, **kwargs):
                return '{\n"responseHeader":{\n"status":0,\n"QTime":425,\n"params":{\n"q":"identifier:2411.08880",\n"fl":"identifier",\n"wt":"json"}},\n"response":{"numFound":1,"start":0,"docs":[\n{\n"identifier":["2024arXiv241108880K",\n"arXiv:2411.08880"]}]\n}}\nformatted string%  "'
        return MockStream()
    
    def connect_get_namespaced_pod_exec(*args, **kwargs):
            return '{\n"responseHeader":{\n"status":0,\n"QTime":425,\n"params":{\n"q":"identifier:2411.08880",\n"fl":"identifier",\n"wt":"json"}},\n"response":{"numFound":1,"start":0,"docs":[\n{\n"identifier":["2024arXiv241108880K",\n"arXiv:2411.08880"]}]\n}}\nformatted string%  "'

class MockStream():
    def __init__(self, *args, **kwargs):
        self.resp = self.connect_get_namespaced_pod_exec(*args, **kwargs)
    def connect_get_namespaced_pod_exec(*args, **kwargs):
        success = kwargs.get("found", True)
        multivalue = kwargs.get("multivalue", False)
        response = kwargs.get("response", True)
        if success and not multivalue:
            return '{\n"responseHeader":{\n"status":0,\n"QTime":425,\n"params":{\n"q":"identifier:2411.08880",\n"fl":"identifier",\n"wt":"json"}},\n"response":{"numFound":1,"start":0,"docs":[\n{\n"identifier":["2024arXiv241108880K",\n"arXiv:2411.08880"]}]\n}}\nformatted string%  "'
        elif multivalue:
            return '{\n"responseHeader":{\n"status":0,\n"QTime":425,\n"params":{\n"q":"identifier:2411.08880",\n"fl":"identifier",\n"wt":"json"}},\n"response":{"numFound":2,"start":0,"docs":[\n{\n"identifier":["2024arXiv241108880K",\n"arXiv:2411.08880"]},\n{\n"identifier":["2024arXiv241108880K",\n"arXiv:2411.08880"]}]\n}}\nformatted string%  "'
        elif response:
            return '{\n"responseHeader":{\n"status":0,\n"QTime":425,\n"params":{\n"q":"identifier:2411.08880",\n"fl":"identifier",\n"wt":"json"}},\n"response":{"numFound":0,"start":0,"docs":[\n{\n"identifier":[]}]\n}}\nformatted string%  "'
        else:
            return '<html>404 not found </html>'
        
class TestkubernetesServices(unittest.TestCase):
    @patch('kubernetes.client.api.core_v1_api.CoreV1Api', side_effect=MockKubernetes, load_instance=True)
    @patch('kubernetes.config.load_kube_config', return_value=Mock())
    def test_successful_read_namepaced_pod_found(self, core_v1, mock_config):
        ads_config={"KUBE_ENV":"Success"}
        identifier='Success'
        with unittest.mock.patch.object(kube_utils, 'stream', return_value=MockStream().resp):
            kube_utils.check_solr_update_status(ads_config, identifier)

    @patch('kubernetes.client.api.core_v1_api.CoreV1Api', side_effect=MockKubernetes, load_instance=True)
    @patch('kubernetes.config.load_kube_config', return_value=Mock())
    def test_successful_read_namepaced_pod_found(self, core_v1, mock_config):
        ads_config={"KUBE_ENV":"Success"}
        identifier='Success'
        with unittest.mock.patch.object(kube_utils, 'stream', return_value=MockStream(multivalue=True).resp):
            kube_utils.check_solr_update_status(ads_config, identifier)

    @patch('kubernetes.client.api.core_v1_api.CoreV1Api', side_effect=MockKubernetes, load_instance=True)
    @patch('kubernetes.config.load_kube_config', return_value=Mock())
    def test_successful_read_namepaced_pod_not_found(self, core_v1, mock_config):
        ads_config={"KUBE_ENV":"Success"}
        identifier='Success'
        with unittest.mock.patch.object(kube_utils, 'stream', return_value=MockStream(found=False).resp):
            kube_utils.check_solr_update_status(ads_config, identifier)

    @patch('kubernetes.client.api.core_v1_api.CoreV1Api', side_effect=MockKubernetes, load_instance=True)
    @patch('kubernetes.config.load_kube_config', return_value=Mock())
    def test_successful_read_namepaced_pod_unsuccessful_get_namespaced_pod_exec(self, core_v1, mock_config):
        ads_config={"KUBE_ENV":"Success"}
        identifier='Success'
        with unittest.mock.patch.object(kube_utils, 'stream', return_value=MockStream(found=False, response=False).resp):
            kube_utils.check_solr_update_status(ads_config, identifier)

    @patch('kubernetes.client.api.core_v1_api.CoreV1Api', side_effect=MockKubernetes, load_instance=True)
    @patch('kubernetes.config.load_kube_config', return_value=Mock())
    def test_unsuccessful_read_namepaced_pod(self, core_v1, mock_config):
        ads_config={"KUBE_ENV":"Failure"}
        identifier='Failure'
        with pytest.raises(ApiException):
            kube_utils.check_solr_update_status(ads_config, identifier)