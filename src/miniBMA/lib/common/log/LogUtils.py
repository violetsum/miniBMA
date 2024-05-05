#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import datetime
import os
import shutil
import stat
import tempfile
from typing import Generator, Union


def get_seconds_until_next_target_time(target_time: Union[str, datetime.datetime]) -> int:
    """计算当前时间（忽略日期）距离下次目标时间的秒数
    如当前时间为12:00:00，目标时间为12:05:00，则返回300秒
    当前时间为12:00:00，目标时间为12:00:00，则返回86400秒
    当前时间为12:06:00，目标时间为12:05:00，则返回86100秒
    """
    # 校验输入参数类型，必须是个字符串
    if not isinstance(target_time, (str, datetime.datetime)):
        raise TypeError(f'Target time should be a string or a datetime object, but got {type(target_time)}')

    # 校验输入参数格式，必须是个合法的时间字符串
    if isinstance(target_time, str):
        try:
            target_datetime = datetime.datetime.strptime(target_time, '%H:%M:%S')
        except ValueError:
            raise ValueError('Invalid time format, should be HH:MM:SS')
    else:
        target_datetime = target_time

    # now = datetime.datetime.now()
    td = datetime.datetime.today()
    target_datetime = target_datetime.replace(year=td.year, month=td.month, day=td.day)
    if target_datetime <= td:
        target_datetime += datetime.timedelta(days=1)

    delta = target_datetime - td
    return int(delta.total_seconds())


def tail(file_path: str, size: int) -> Generator[bytes, None, None]:
    """读取文件末尾内容，按行返回，返回内容的总大小不超过size字节"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File not found: {file_path}')

    file_size = os.path.getsize(file_path)
    if file_size <= size:
        with open(file_path, 'rb') as f:
            # 直接返回整个文件
            yield from f
        return

    with open(file_path, 'rb') as f:
        # 定位到倒数第size+1个字节的位置
        f.seek(file_size - size - 1)
        # 如果倒数第size+1个字节是换行符，则直接返回后面的内容
        if f.read(1) == b'\n':
            yield from f
            return

        # 如果倒数第size个字节是换行符，则直接返回后面的内容
        if f.read(1) == b'\n':
            yield from f
            return

        # 说明倒数第size个字节不是换行符，即在某一行中间，跳过这一行，直接返回后面的内容
        f.readline()
        yield from f


def backup_and_truncate_file(file_path: str, max_size: int):
    """备份文件并截断文件，使得文件大小不超过max_size字节"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File not found: {file_path}')

    # 备份文件
    backup_file_path = f'{file_path}.1'
    shutil.copyfile(file_path, backup_file_path)

    # 将原文件清空
    os.truncate(file_path, 0)

    backup_file_size = os.path.getsize(backup_file_path)
    if backup_file_size <= max_size:
        # 备份文件大小小于等于max_size，不需要截断，将文件权限设置为只读，直接返回
        os.chmod(backup_file_path, stat.S_IREAD)
        return

    with tempfile.NamedTemporaryFile(mode='wb', delete=True) as temp_file:
        for line in tail(backup_file_path, max_size):
            temp_file.write(line)

        temp_file.flush()
        shutil.copyfile(temp_file.name, backup_file_path)
        os.chmod(backup_file_path, stat.S_IREAD)


if __name__ == '__main__':
    # 使用示例
    import sys
    file_path = 'a.txt'  # 替换为你的文件路径
    size = int(sys.argv[1])  # 需要返回的字节大小
    backup_and_truncate_file(file_path, size)

    # count = 0
    # for line in tail(file_path, size):
    #     count += len(line)
    #     print(line)  # 打印每一行

    # print(f'Total size: {count}')