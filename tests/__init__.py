"""Tests for the dlib_face_recognition component."""

def pytest_configure(config):
    config.addinivalue_line("markers", "data_persistence")
    config.addinivalue_line("markers", "list_data_persistence")
    config.addinivalue_line("markers", "local_json_file_list_data_persistence")
