The program that basically relays messages from Discord to Slack and vice versa, crafted for COMP3988 at USYD.

It is recommended to create a Python virtual environment before running.

```
python3 -m venv <name>
```

Then 

```
source <name>/bin/activate
```

Afterwards, run

```
pip install -r requirements.txt
```

Remember to get the required tokens/credentials and put them into `env_var.sh` and run the command to export environment variables.

```
source env_var.sh
```

Also remember to change the entries in config.py accordingly.


Finally, to run, use the command

```
python3 main.py
```
