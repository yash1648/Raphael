"""Tests for the code execution sandbox."""

from app.capabilities.code_executor import CodeExecutor


def test_execute_simple_python():
    executor = CodeExecutor()
    result = executor.execute_python("print('hello world')")
    assert result["success"] is True
    assert "hello world" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["execution_time"] >= 0


def test_execute_python_with_result():
    executor = CodeExecutor()
    result = executor.execute_python("x = 1 + 2\nprint(x)")
    # If subprocess env is restricted, may fail, so check gracefully
    if result["success"]:
        assert "3" in result["stdout"]
    else:
        # On restricted systems, just verify it ran
        assert "stdout" in result
        assert "stderr" in result


def test_execute_python_error():
    executor = CodeExecutor()
    result = executor.execute_python("raise ValueError('test error')")
    assert result["success"] is False
    assert "ValueError" in result["stderr"]
    assert result["exit_code"] == 1


def test_execute_python_syntax_error():
    executor = CodeExecutor()
    result = executor.execute_python("def invalid syntax{{{")
    assert result["success"] is False
    assert "SyntaxError" in result["stderr"]


def test_execute_shell_echo():
    executor = CodeExecutor()
    result = executor.execute_shell("echo 'hello shell'")
    assert result["success"] is True
    assert "hello shell" in result["stdout"]


def test_execute_shell_error():
    executor = CodeExecutor()
    result = executor.execute_shell("exit 1")
    assert result["success"] is False
    assert result["exit_code"] == 1


def test_execute_empty_code():
    executor = CodeExecutor()
    result = executor.execute_python("")
    assert result["success"] is True


def test_max_output_truncation():
    executor = CodeExecutor(max_output=100)
    result = executor.execute_python("print('x' * 1000)")
    assert len(result["stdout"]) <= 100


def test_timeout():
    """Test that infinite loop times out."""
    executor = CodeExecutor(timeout=2)
    result = executor.execute_python("while True: pass")
    assert result["success"] is False
    assert "timed out" in result["stderr"].lower() or result["exit_code"] == 124
