A simple application to popup a window to remind the user of something they need to if they haven't done it yet.

# Usage

This application relies on a `config.yaml` file. The file must be located in the same location as the script is run.

# config.yaml options

## popup

This section handles popup messages. Below is an example.

```yaml
popup:
  - glasses:
    message: Are you wearing your glasses??
    interval: 10
    unit: seconds
    start: '12:10'
```

* `glasses` : just the title of the section, it is not used.
* `message` : the message to display
* `interval` : how often to display the message
* `unit` : can be ither minutes or seconds
* `start` (optional) : provide a HH:MM time to start from for calculating all intervals. Otherwise the popup event on the interval tied to program startup. This option is to provide the ability to have something popup at the top of the hour by setting `'12:00'` for `start`, `interval` to `60`, and `unit` to `minutes`.

If the `start` time is in the future, say `13:00`, then nothing will happen until `13:00`. So if the current time is `08:00` nothing will be displayed until `13:00` is reached then it will continue after that at the regular interval. This value just sets when times to run are initially calculated.

Set `start` to `00:mm` to have run at the expected minutes offset for the entire day regardless of when you start the program.

