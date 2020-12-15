"""Test fixtures for the dlib_face_recognition component."""

def pytest_configure(config):
    config.addinivalue_line("markers", "data_container")
    config.addinivalue_line("markers", "data_container_with_max_size")
    config.addinivalue_line("markers", "dict_data_container")
    config.addinivalue_line("markers", "dict_data_container_with_max_size")
    config.addinivalue_line("markers", "local_json_file_dict_data_persistence")
    config.addinivalue_line("markers", "fs_storage")
