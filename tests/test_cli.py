from unittest.mock import Mock, patch

from macrosignage import cli


def test_prod_main_serves_with_waitress_options():
    app = object()
    serve = Mock()

    with (
        patch.object(cli, "create_app", return_value=app),
        patch("waitress.serve", serve),
    ):
        exit_code = cli.prod_main(["--host", "127.0.0.1", "--port", "9090", "--threads", "8"])

    assert exit_code == 0
    serve.assert_called_once_with(app, host="127.0.0.1", port=9090, threads=8)


def test_prod_subcommand_uses_same_waitress_options():
    app = object()
    serve = Mock()

    with (
        patch.object(cli, "create_app", return_value=app),
        patch("waitress.serve", serve),
    ):
        exit_code = cli.main(["prod", "--host", "127.0.0.1", "--port", "9090", "--threads", "8"])

    assert exit_code == 0
    serve.assert_called_once_with(app, host="127.0.0.1", port=9090, threads=8)
