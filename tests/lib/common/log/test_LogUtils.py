#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import datetime
import os
from pathlib import Path
import tempfile

import pytest
from pytest_mock import MockerFixture

from miniBMA.lib.common.log.LogUtils import backup_and_truncate_file, get_seconds_until_next_target_time, tail


class MockDateTime(datetime.datetime):
    pass


class TestGetSecondsUntilNextTargetTime:
    @staticmethod
    @pytest.mark.parametrize(
        "mock_today_value, target_time, expected_seconds",
        [
            (datetime.datetime(2022, 1, 1, 0, 0, 0), "00:00:00", 86400),
            (datetime.datetime(2023, 1, 1, 0, 0, 0), MockDateTime(2023, 1, 1, 23, 59, 59), 86399),
            (datetime.datetime(2024, 1, 1, 0, 0, 0), "00:00:01", 1),
        ],
    )
    def test_get_seconds_until_next_target_time(mock_today_value, target_time, expected_seconds, mocker: MockerFixture):
        """Test get_seconds_until_next_target_time."""
        mocker.patch.object(MockDateTime, 'today', return_value=mock_today_value)
        mocker.patch.object(datetime, 'datetime', MockDateTime)
        assert get_seconds_until_next_target_time(target_time) == expected_seconds

    @staticmethod
    @pytest.mark.parametrize("target_time", ["24:00:00", "25:00:00"])
    def test_get_seconds_until_next_target_time_invalid_target_time(target_time):
        """Test get_seconds_until_next_target_time with invalid target_time."""
        with pytest.raises(ValueError):
            get_seconds_until_next_target_time(target_time)

    @staticmethod
    @pytest.mark.parametrize("target_time", [None, 123])
    def test_get_seconds_until_next_target_time_invalid_target_time_type(target_time):
        """Test get_seconds_until_next_target_time with invalid target_time type."""
        with pytest.raises(TypeError):
            get_seconds_until_next_target_time(target_time)


class TestTail:
    def setup_class(self):
        self.test_file = tempfile.NamedTemporaryFile(mode='w', delete=False)

    def teardown_class(self):
        os.remove(self.test_file.name)

    @staticmethod
    def test_file_not_found():
        with pytest.raises(FileNotFoundError):
            list(tail('non_existent_file.txt', 100))

    @pytest.mark.parametrize(
        "file_content, tail_size, expected_tail_content",
        [
            ("a\nb\nc\n", 100, ["a\n", "b\n", "c\n"]),
            ("a\nb\nc\n", 6, ["a\n", "b\n", "c\n"]),
            ("a\nb\nc\n", 5, ["b\n", "c\n"]),
            ("", 0, []),
        ],
    )
    def test_file_exist(self, file_content, tail_size, expected_tail_content):
        with open(self.test_file.name, 'w') as f:
            f.write(file_content)

        result = list(map(bytes.decode, tail(self.test_file.name, tail_size)))
        assert result == expected_tail_content


class TestBackupAndTruncateFile:
    def setup_class(self):
        self.test_file = "test.txt"

    def teardown_class(self):
        os.remove(self.test_file)
        if os.path.exists(f"{self.test_file}.1"):
            os.remove(f"{self.test_file}.1")

    def setup_method(self):
        if os.path.exists(f"{self.test_file}.1"):
            os.remove(f"{self.test_file}.1")

    @staticmethod
    def test_file_not_found():
        with pytest.raises(FileNotFoundError):
            backup_and_truncate_file("non_existent_file.txt", 100)

    @pytest.mark.parametrize(
        "old_file_content, truncate_size, expected_backup_file_content",
        [
            ("a\nb\nc\n", 100, "a\nb\nc\n"),
            ("a\nb\nc\n", 6, "a\nb\nc\n"),
            ("a\nb\nc\n", 5, "b\nc\n"),
            ("", 0, ""),
        ],
    )
    def test_file_exist(self, old_file_content, truncate_size, expected_backup_file_content):
        with open(self.test_file, 'w') as f:
            f.write(old_file_content)

        backup_and_truncate_file(self.test_file, truncate_size)

        assert Path(f"{self.test_file}").read_text() == ""
        assert Path(f"{self.test_file}.1").read_text() == expected_backup_file_content
        # 备份文件权限为400
        assert oct(os.stat(f"{self.test_file}.1").st_mode & 0o777) == "0o400"
