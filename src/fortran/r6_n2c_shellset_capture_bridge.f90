! Candidate-only ShellSet bridge for the N2C-W1 synthetic snapshot writer.
!
! Runtime invocation authority is not currently available at this call site.
! Consequently CAPTURE_ONLY is deliberately rejected before serialization.
module r6_n2c_shellset_capture_bridge
  use iso_fortran_env, only: int64, real64
  use r6_sparse_snapshot_writer, only: capture_config, capture_context, &
      write_a0b0_snapshot, CAPTURE_DEFAULT_OFF, CAPTURE_FAILED, &
      MODE_DEFAULT_OFF, MODE_CAPTURE_ONLY
  implicit none
  private
  public :: n2c_capture_pre_solver

contains

  subroutine n2c_capture_pre_solver(ab, b0, i_diagonal, model_num, process_rank, &
                                    rpeat, iteration, fem_call_ordinal, &
                                    solver_may_proceed, message)
    real(real64), intent(in) :: ab(:,:), b0(:)
    integer, intent(in) :: i_diagonal
    integer, intent(in) :: model_num, process_rank, rpeat, iteration, fem_call_ordinal
    logical, intent(out) :: solver_may_proceed
    character(len=*), intent(out) :: message
    type(capture_config) :: config
    type(capture_context) :: context
    character(len=32) :: requested_mode
    integer :: env_status, env_length, writer_status
    integer(int64) :: n, ldab, diagonal, kl, ku

    solver_may_proceed = .false.
    message = 'N2C capture gate failed closed'
    requested_mode = ''
    call get_environment_variable('ARCANA_N2C_CAPTURE_MODE', requested_mode, &
                                  length=env_length, status=env_status)

    ! Missing variable alone means DEFAULT_OFF. Truncation or other lookup
    ! errors are configuration failures and must not open the Solver gate.
    if (env_status == 1) then
      config%mode = MODE_DEFAULT_OFF
    else if (env_status /= 0) then
      config%mode = -1
    else if (env_length == 0) then
      config%mode = -1
    else if (trim(requested_mode) == 'DEFAULT_OFF') then
      config%mode = MODE_DEFAULT_OFF
    else if (trim(requested_mode) == 'CAPTURE_ONLY') then
      config%mode = MODE_CAPTURE_ONLY
    else
      config%mode = -1
    end if

    if (config%mode == MODE_DEFAULT_OFF) then
      ! W1 returns before inspecting the arrays or probing an output path.
      call write_a0b0_snapshot(ab, b0, 0_int64, 0_int64, 0_int64, &
                               config, context, writer_status, message)
      solver_may_proceed = writer_status == CAPTURE_DEFAULT_OFF
      return
    end if

    if (config%mode /= MODE_CAPTURE_ONLY) then
      message = 'unsupported N2C capture mode; Solver is blocked'
      return
    end if

    if (model_num < 1 .or. process_rank < 1 .or. rpeat < 1 .or. &
        iteration < 1 .or. fem_call_ordinal < 1) then
      message = 'incomplete local ShellSet invocation fields; Solver is blocked'
      return
    end if

    ! The live ShellSet call graph has not supplied an authoritative context,
    ! payload path, or independently bound source-value digest. Leave context
    ! empty on purpose: W1 must reject it before creating a file. Do not turn
    ! ThID or caller-provided labels into provenance.
    n = int(size(ab,2), int64)
    ldab = int(size(ab,1), int64)
    diagonal = int(i_diagonal, int64)
    if (n < 1_int64 .or. diagonal < 1_int64 .or. diagonal > ldab) then
      message = 'invalid ShellSet band dimensions; Solver is blocked'
      return
    end if
    kl = ldab - diagonal
    ku = 2_int64 * diagonal - ldab - 1_int64
    if (kl < 0_int64 .or. ku < 0_int64 .or. &
        2_int64 * kl + ku + 1_int64 /= ldab .or. &
        size(b0) /= size(ab,2)) then
      message = 'inconsistent ShellSet band/RHS dimensions; Solver is blocked'
      return
    end if

    call write_a0b0_snapshot(ab, b0, n, kl, ku, config, context, &
                             writer_status, message)
    if (writer_status == CAPTURE_FAILED) return
    ! No W1 status authorizes entering Solver. This includes any unexpected
    ! future status; CAPTURE_ONLY_STOP_REQUIRED is also terminal.
    message = 'capture did not establish an authorized Solver continuation'
  end subroutine n2c_capture_pre_solver

end module r6_n2c_shellset_capture_bridge
