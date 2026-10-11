! Synthetic driver for the bounded standalone W1 writer; never linked to ShellSet.
program r6_n2c_capture_driver
  use iso_fortran_env, only: int32, int64, real64
  use ieee_arithmetic, only: ieee_value, ieee_quiet_nan
  use r6_sparse_snapshot_writer
  implicit none
  character(len=32) :: mode, shape_case
  character(len=1024) :: output_path, solver_marker
  character(len=64) :: digest
  character(len=32) :: arg
  integer(int64) :: n, kl, ku, ldab, i, j, row
  integer :: argc, ios, status
  character(len=192) :: message
  real(real64), allocatable :: ab(:,:), b0(:)
  integer(int64) :: bits
  type(capture_config) :: config
  type(capture_context) :: context

  argc = command_argument_count()
  if (argc /= 8) error stop 41
  call get_command_argument(1,mode)
  call get_command_argument(2,arg)
  read(arg,*,iostat=ios) n
  if (ios /= 0) error stop 42
  call get_command_argument(3,arg)
  read(arg,*,iostat=ios) kl
  if (ios /= 0) error stop 43
  call get_command_argument(4,arg)
  read(arg,*,iostat=ios) ku
  if (ios /= 0) error stop 44
  call get_command_argument(5,output_path)
  call get_command_argument(6,digest)
  call get_command_argument(7,shape_case)
  call get_command_argument(8,solver_marker)

  if (n < 1 .or. n > 2048 .or. kl < 0 .or. ku < 0 .or. kl >= n .or. ku >= n) error stop 45
  ldab = 2_int64*kl + ku + 1_int64
  if (trim(shape_case) == 'BAD_SHAPE') ldab = ldab - 1_int64
  allocate(ab(int(ldab),int(n)),b0(int(n)))
  ab = 0.0_real64
  do i = 0_int64, n-1_int64
    do j = max(0_int64,i-kl), min(n-1_int64,i+ku)
      row = kl + ku + 1_int64 + i - j
      if (row <= ldab .and. i == 0_int64 .and. j == 1_int64) then
        bits = int(z'8000000000000000',int64)
        ab(int(row),int(j+1_int64)) = transfer(bits,0.0_real64)
      else if (row <= ldab .and. i == 1_int64 .and. j == 0_int64 .and. kl >= 1_int64) then
        bits = 1_int64
        ab(int(row),int(j+1_int64)) = transfer(bits,0.0_real64)
      else if (row <= ldab .and. i == j) then
        ab(int(row),int(j+1_int64)) = real(i+2_int64,real64)
      else if (row <= ldab .and. mod(i+j,3_int64) /= 0_int64) then
        ab(int(row),int(j+1_int64)) = real(10_int64*i-j+1_int64,real64)/8.0_real64
      end if
    end do
    if (i == 0_int64) then
      bits = int(z'8000000000000000',int64)
      b0(int(i+1_int64)) = transfer(bits,0.0_real64)
    else
      b0(int(i+1_int64)) = real(2_int64*i-3_int64,real64)/4.0_real64
    end if
  end do
  if (trim(shape_case) == 'NONFINITE') ab(int(kl+ku+1_int64),1) = ieee_value(0.0_real64,ieee_quiet_nan)

  context%test_only = .true.
  context%run_id = 'TEST_ONLY:run-1'
  context%model_id = 'TEST_ONLY:model-1'
  context%rank = 1_int32
  context%rpeat = 1_int32
  context%fem_iteration = 1_int32
  context%fem_call_ordinal = 1_int32
  context%source_id = 'TEST_ONLY:source-fixture'
  context%input_id = 'TEST_ONLY:input-fixture'
  context%dof_order_id = 'TEST_ONLY:dof-fixture'
  if (trim(shape_case) == 'BAD_CONTEXT') context%input_id = ''
  config%temporary_path = trim(output_path)
  config%source_value_sha256 = trim(digest)
  if (trim(mode) == 'DEFAULT_OFF') then
    config%mode = MODE_DEFAULT_OFF
  else
    config%mode = MODE_CAPTURE_ONLY
  end if

  call write_a0b0_snapshot(ab,b0,n,kl,ku,config,context,status,message)
  write(*,'(A,I0)') 'CAPTURE_STATUS=',status
  write(*,'(A,A)') 'CAPTURE_MESSAGE=',trim(message)
  if (status == CAPTURE_DEFAULT_OFF .or. status == CAPTURE_ONLY_STOP_REQUIRED .or. status == CAPTURE_FAILED) stop 0
  call mark_solver_called(trim(solver_marker))

contains

  subroutine mark_solver_called(path)
    character(len=*), intent(in) :: path
    integer :: u, e
    open(newunit=u,file=path,status='new',action='write',iostat=e)
    if (e /= 0) error stop 46
    write(u,'(A)',iostat=e) 'UNREACHABLE_SOLVER_MARKER'
    close(u)
    error stop 47
  end subroutine mark_solver_called

end program r6_n2c_capture_driver
