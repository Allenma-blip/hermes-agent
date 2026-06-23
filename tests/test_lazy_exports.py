# 简单单元测试：确保包根暴露名存在且在访问时触发懒加载
import importlib
import sys


def test_lazy_export_not_imported_by_default(monkeypatch):
    # 重新加载包以确保清洁状态
    if "gateway.platforms" in sys.modules:
        del sys.modules["gateway.platforms"]
    gp = importlib.import_module("gateway.platforms")
    # 在未访问属性前，不应有 qqbot 或 yuanbao 模块被导入（粗略检测）
    assert not any(m.startswith("gateway.platforms.qqbot") for m in sys.modules)
    assert not any(m.startswith("gateway.platforms.yuanbao") for m in sys.modules)

    # 访问属性，触发懒加载
    assert hasattr(gp, "QQAdapter")
    _ = gp.QQAdapter  # 触发实际导入
    assert "gateway.platforms.qqbot" in sys.modules
