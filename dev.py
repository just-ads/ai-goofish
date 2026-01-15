#!/usr/bin/env python3
"""
AI Goofish 快速启动脚本
一键启动前端和后端开发服务器
"""
import os
import platform
import signal
import subprocess
import sys
from pathlib import Path


class DevServer:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent

    def check_dependencies(self):
        """检查依赖是否已安装"""
        # 检查 Python 依赖
        if not (self.project_root / ".venv").exists() and not (self.project_root / "venv").exists():
            print("❌ Python 虚拟环境不存在")
            print("📦 正在创建虚拟环境并安装依赖...")
            self.install_backend_deps()
        else:
            print("✅ Python 虚拟环境已存在")

        # 检查前端依赖
        if not (self.project_root / "webui" / "node_modules").exists():
            print("❌ 前端依赖未安装")
            print("📦 正在安装前端依赖...")
            self.install_frontend_deps()
        else:
            print("✅ 前端依赖已安装")

    def install_backend_deps(self):
        """安装后端依赖"""
        venv_python = self.get_venv_python()
        subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    def install_frontend_deps(self):
        """安装前端依赖"""
        webui_dir = self.project_root / "webui"
        subprocess.run(["npm", "install"], cwd=webui_dir, check=True, shell=True)

    def get_venv_python(self):
        """获取虚拟环境的 Python 路径"""
        if platform.system() == "Windows":
            if (self.project_root / ".venv" / "Scripts" / "python.exe").exists():
                return str(self.project_root / ".venv" / "Scripts" / "python.exe")
            elif (self.project_root / "venv" / "Scripts" / "python.exe").exists():
                return str(self.project_root / "venv" / "Scripts" / "python.exe")
        else:
            if (self.project_root / ".venv" / "bin" / "python").exists():
                return str(self.project_root / ".venv" / "bin" / "python")
            elif (self.project_root / "venv" / "bin" / "python").exists():
                return str(self.project_root / "venv" / "bin" / "python")
        return sys.executable

    def start_backend(self):
        """启动后端服务器"""
        venv_python = self.get_venv_python()
        print(f"🚀 启动后端服务 (Python: {venv_python})...")
        env = os.environ.copy()
        env['DEV'] = '1'
        env['DEBUG'] = '1'
        backend_process = subprocess.Popen(
            [venv_python, "start.py"],
            cwd=self.project_root,
            env=env
        )
        self.processes.append(("backend", backend_process))
        return backend_process

    def start_frontend(self):
        """启动前端开发服务器"""
        webui_dir = self.project_root / "webui"
        print(f"🎨 启动前端开发服务器...")
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=webui_dir,
            shell=True
        )
        self.processes.append(("frontend", frontend_process))
        return frontend_process

    def cleanup(self, signum=None, frame=None):
        """清理进程"""
        print("\n\n🛑 正在停止服务...")
        for name, process in self.processes:
            if process.poll() is None:
                print(f"  停止 {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ 所有服务已停止")
        sys.exit(0)

    def run(self):
        """运行开发服务器"""
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.cleanup)
        if platform.system() != "Windows":
            signal.signal(signal.SIGTERM, self.cleanup)

        print("=" * 50)
        print("  AI Goofish 开发环境启动器")
        print("=" * 50)

        # 检查依赖
        print("\n📋 检查依赖...")
        self.check_dependencies()

        # 启动服务
        print("\n🚀 启动服务...")
        self.start_backend()
        self.start_frontend()

        print("\n" + "=" * 50)
        print("✅ 开发环境已启动！")
        print("=" * 50)
        print("\n📌 服务地址：")
        print("  • 后端 API: http://127.0.0.1:8000")
        print("  • 前端界面: http://127.0.0.1:5173")
        print("  • API 文档: http://127.0.0.1:8000/docs")
        print("\n💡 提示：按 Ctrl+C 停止所有服务")
        print("=" * 50 + "\n")

        # 等待进程
        try:
            for name, process in self.processes:
                process.wait()
        except KeyboardInterrupt:
            self.cleanup()


if __name__ == "__main__":
    server = DevServer()
    server.run()
