import aiofiles
from pathlib import Path
import asyncio
import os
from typing import Optional


async def cleanup_temp_file(temp_path: str):
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except:
        pass


class FileOperator:
    def __init__(self, filepath: str):
        self.filepath = str(Path(filepath).absolute())
        self._lock = asyncio.Lock()
        self._ensure_parent_dir()

    def _ensure_parent_dir(self):
        parent_dir = Path(self.filepath).parent
        parent_dir.mkdir(parents=True, exist_ok=True)

    async def read(self) -> Optional[str]:
        async with self._lock:
            try:
                async with aiofiles.open(self.filepath, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return content if content.strip() else None
            except FileNotFoundError:
                return None
            except PermissionError as e:
                raise PermissionError(f"没有权限读取文件 {self.filepath}") from e
            except (IOError, OSError) as e:
                raise IOError(f"读取文件 {self.filepath} 时发生错误: {e}") from e

    async def write(self, content: str) -> None:
        async with self._lock:
            temp_path = f"{self.filepath}.{os.getpid()}.{id(self)}.tmp"

            try:
                async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                os.replace(temp_path, self.filepath)

            except PermissionError as e:
                await cleanup_temp_file(temp_path)
                raise PermissionError(f"没有权限写入文件 {self.filepath}") from e
            except (IOError, OSError) as e:
                await cleanup_temp_file(temp_path)
                raise IOError(f"写入文件 {self.filepath} 时发生错误: {e}") from e

    async def delete(self) -> None:
        async with self._lock:
            try:
                if os.path.exists(self.filepath):
                    os.remove(self.filepath)
            except PermissionError as e:
                raise PermissionError(f"没有权限删除文件 {self.filepath}") from e
            except (IOError, OSError) as e:
                raise IOError(f"删除文件 {self.filepath} 时发生错误: {e}") from e
