rust = import('rust')

_trace_rs = static_library(
  'trace',
  'src/lib.rs',
  override_options: ['rust_std=2021', 'build.rust_std=2021'],
  rust_abi: 'rust',
  dependencies: [libc_rs,qemuutil_rs],
)

trace_rs = declare_dependency(link_with: _trace_rs)

trace_rs_lib = static_library(
  'qemu-trace',             # Library name
  trace_rs_targets,         # List of generated `.rs` custom targets
  rust_crate_type : 'staticlib',
  install : false,
  dependencies : [],        # Add any necessary Rust dependencies if needed
)

