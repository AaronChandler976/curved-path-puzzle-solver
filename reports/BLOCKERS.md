# Blockers (overnight run 01)

None need sudo so far. All packages were installed with pip inside `disasm` (spatialmath-python, rtree, tqdm, pymcubes, libigl).

## Non-sudo issues found (worked around)
- The shell `PYTHONPATH` points at ROS (`/opt/ros/lyrical/...python3.14`). pytest loads its `launch_testing` plugin and crashes
  (`ModuleNotFoundError: osrf_pycommon`; `experiments/2026-11-22_pytest_oracle/stdout_attempt1_ros_plugin.log`). Workaround:
  run pytest with `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`. Possible fix: don't export ROS paths in the shell used for this project.
- Not attempted: building ATA's C++ simulator (needed for ATA cheap-oracle labels). See MORNING_REPORT night-02 plan.
