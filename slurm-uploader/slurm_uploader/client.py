
from paramiko import SSHClient, AutoAddPolicy


class SFTPClient:

    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int = 22,
    ):
        self.username = username
        self.password = password
        self.hostname = host
        self.port = port

    def __enter__(self):

        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        self.ssh_client.connect(
            self.hostname,
            self.port,
            self.username,
            self.password,
        )

        self.sftp_client = self.ssh_client.open_sftp()

    def __exit__(self, *args, **kwargs):

        self.ssh_client.close()
        self.sftp_client.close()

