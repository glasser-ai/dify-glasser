from dify_plugin import DifyPluginEnv, Plugin

# 240s: a run may wait for an async endpoint to settle (see tools/run.py);
# the default 120s leaves no headroom above the longest published timeout.
plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=240))

if __name__ == "__main__":
    plugin.run()
