! Bounded, standalone ARCNSNP1 writer for synthetic fixtures only.
! This module is not linked to ShellSet and never calls a solver.
module r6_sparse_snapshot_writer
  use iso_fortran_env, only: int8, int32, int64, real64
  use ieee_arithmetic, only: ieee_is_finite, ieee_support_datatype
  implicit none
  private

  integer, parameter, public :: CAPTURE_DEFAULT_OFF = 0
  integer, parameter, public :: CAPTURE_ONLY_STOP_REQUIRED = 1
  integer, parameter, public :: CAPTURE_FAILED = 2
  integer, parameter, public :: MODE_DEFAULT_OFF = 0
  integer, parameter, public :: MODE_CAPTURE_ONLY = 1
  integer(int64), parameter :: MAX_N = 2048_int64
  integer(int64), parameter :: MAX_STORAGE = 2000000_int64
  character(len=8), parameter :: MAGIC = 'ARCNSNP1'

  type, public :: capture_config
    integer :: mode = MODE_DEFAULT_OFF
    character(len=1024) :: temporary_path = ''
    character(len=64) :: source_value_sha256 = ''
  end type capture_config

  type, public :: capture_context
    logical :: test_only = .false.
    character(len=128) :: run_id = ''
    character(len=128) :: model_id = ''
    integer(int32) :: rank = 0_int32
    integer(int32) :: rpeat = 0_int32
    integer(int32) :: fem_iteration = 0_int32
    integer(int32) :: fem_call_ordinal = 0_int32
    character(len=128) :: source_id = ''
    character(len=128) :: input_id = ''
    character(len=128) :: dof_order_id = ''
  end type capture_context

  public :: write_a0b0_snapshot

contains

  subroutine write_a0b0_snapshot(ab, b0, n, kl, ku, config, context, status, message)
    real(real64), intent(in) :: ab(:,:), b0(:)
    integer(int64), intent(in) :: n, kl, ku
    type(capture_config), intent(in) :: config
    type(capture_context), intent(in) :: context
    integer, intent(out) :: status
    character(len=*), intent(out) :: message
    integer(int64) :: ldab, storage_count, record_count, i, j, row, col, bits
    integer :: unit, ios, close_ios, hex_ios, hex_pos
    integer :: u32_n, u32_kl, u32_ku, u32_count
    logical :: opened
    integer(int8) :: byte_value

    status = CAPTURE_FAILED
    message = 'capture failed before output was accepted'
    opened = .false.
    unit = -1

    ! Disabled means no path checks, file probes, writes, or array reads.
    if (config%mode == MODE_DEFAULT_OFF) then
      status = CAPTURE_DEFAULT_OFF
      message = 'default-off: no capture side effect'
      return
    end if
    if (config%mode /= MODE_CAPTURE_ONLY) then
      message = 'unsupported mode; no solve-capable mode exists'
      return
    end if

    if (.not. context_is_test_only(context)) then
      message = 'incomplete or non-TEST_ONLY context is not accepted by W1'
      return
    end if
    if (.not. valid_sha256_hex(config%source_value_sha256)) then
      message = 'source-value SHA256 must be 64 hexadecimal characters'
      return
    end if
    if (len_trim(config%temporary_path) < 5) then
      message = 'a new .tmp output path is required'
      return
    end if
    if (config%temporary_path(len_trim(config%temporary_path)-3:len_trim(config%temporary_path)) /= '.tmp') then
      message = 'capture path must use the non-authoritative .tmp suffix'
      return
    end if
    if (n < 1_int64 .or. n > MAX_N .or. kl < 0_int64 .or. ku < 0_int64) then
      message = 'dimensions outside bounded synthetic scope'
      return
    end if
    if (kl >= n .or. ku >= n) then
      message = 'bandwidth must be smaller than matrix dimension'
      return
    end if
    ! n is capped before these products, so the following int64 arithmetic is bounded.
    ldab = 2_int64 * kl + ku + 1_int64
    storage_count = ldab * n
    if (storage_count > MAX_STORAGE) then
      message = 'band storage exceeds bounded synthetic cap'
      return
    end if
    if (int(size(ab,1),int64) /= ldab .or. int(size(ab,2),int64) /= n) then
      message = 'AB shape does not match n, KL, KU and DGBSV LDAB'
      return
    end if
    if (int(size(b0),int64) /= n) then
      message = 'RHS length does not match n'
      return
    end if
    if (.not. is_contiguous(ab) .or. .not. is_contiguous(b0)) then
      message = 'noncontiguous inputs are rejected to avoid hidden copy-in temporaries'
      return
    end if
    if (storage_size(0.0_real64) /= 64 .or. storage_size(0_int64) /= 64 .or. &
        storage_size(0_int32) /= 32 .or. storage_size(0_int8) /= 8 .or. &
        storage_size('A') /= 8 .or. .not. ieee_support_datatype(0.0_real64) .or. &
        radix(0.0_real64) /= 2 .or. digits(0.0_real64) /= 53 .or. &
        maxexponent(0.0_real64) /= 1024 .or. minexponent(0.0_real64) /= -1021) then
      message = 'required 8-bit bytes, int32, int64, or IEEE binary64 unavailable'
      return
    end if

    record_count = 0_int64
    do j = 0_int64, n - 1_int64
      do i = max(0_int64,j-ku), min(n-1_int64,j+kl)
        row = kl + ku + 1_int64 + i - j
        bits = transfer(ab(int(row),int(j+1_int64)), 0_int64)
        if (.not. ieee_is_finite(ab(int(row),int(j+1_int64)))) then
          message = 'nonfinite logical matrix coefficient'
          return
        end if
        if (bits /= 0_int64) record_count = record_count + 1_int64
      end do
    end do
    ! Validate all storage: logical-band entries are finite; fill/padding is zero.
    do col = 0_int64, n - 1_int64
      do row = 1_int64, ldab
        i = row - (kl + ku + 1_int64) + col
        if (i >= 0_int64 .and. i < n .and. -ku <= i-col .and. i-col <= kl) cycle
        bits = transfer(ab(int(row),int(col+1_int64)), 0_int64)
        if (iand(bits,int(z'7FFFFFFFFFFFFFFF',int64)) /= 0_int64) then
          message = 'nonzero reserved/fill/padding entry is not A0'
          return
        end if
      end do
    end do
    do i = 1_int64, n
      if (.not. ieee_is_finite(b0(int(i)))) then
        message = 'nonfinite RHS value'
        return
      end if
    end do
    if (record_count > MAX_STORAGE .or. record_count > int(huge(0_int32),int64)) then
      message = 'sparse record count exceeds wire-format capacity'
      return
    end if
    u32_n = int(n,int32)
    u32_kl = int(kl,int32)
    u32_ku = int(ku,int32)
    u32_count = int(record_count,int32)

    open(newunit=unit, file=trim(config%temporary_path), status='new', &
         access='stream', form='unformatted', action='write', iostat=ios)
    if (ios /= 0) then
      message = 'cannot create new temporary output (collision or I/O error)'
      return
    end if
    opened = .true.
    write(unit,iostat=ios) MAGIC
    if (ios /= 0) goto 900
    call write_u32(unit,u32_n,ios)
    if (ios /= 0) goto 900
    call write_u32(unit,u32_kl,ios)
    if (ios /= 0) goto 900
    call write_u32(unit,u32_ku,ios)
    if (ios /= 0) goto 900
    call write_u32(unit,u32_count,ios)
    if (ios /= 0) goto 900
    do hex_pos = 1, 64, 2
      read(config%source_value_sha256(hex_pos:hex_pos+1),'(Z2)',iostat=hex_ios) u32_n
      if (hex_ios /= 0) goto 900
      call signed_byte(int(u32_n,int64),byte_value)
      write(unit,iostat=ios) byte_value
      if (ios /= 0) goto 900
    end do
    do i = 0_int64, n - 1_int64
      do j = max(0_int64,i-kl), min(n-1_int64,i+ku)
        row = kl + ku + 1_int64 + i - j
        bits = transfer(ab(int(row),int(j+1_int64)),0_int64)
        if (bits == 0_int64) cycle
        call write_u32(unit,int(i,int32),ios)
        if (ios /= 0) goto 900
        call write_u32(unit,int(j,int32),ios)
        if (ios /= 0) goto 900
        call write_u64(unit,bits,ios)
        if (ios /= 0) goto 900
      end do
    end do
    do i = 1_int64, n
      bits = transfer(b0(int(i)),0_int64)
      call write_u64(unit,bits,ios)
      if (ios /= 0) goto 900
    end do
    flush(unit,iostat=ios)
    if (ios /= 0) goto 900
    close(unit,iostat=close_ios)
    opened = .false.
    if (close_ios /= 0) then
      message = 'close failed; temporary output remains non-authoritative'
      return
    end if
    status = CAPTURE_ONLY_STOP_REQUIRED
    message = 'payload written and closed; external oracle verification required; stop before solver'
    return

900 continue
    if (opened) then
      close(unit,iostat=close_ios)
      opened = .false.
    end if
    status = CAPTURE_FAILED
    message = 'write/serialization/flush failure; partial output is non-authoritative'
  end subroutine write_a0b0_snapshot

  logical function context_is_test_only(context)
    type(capture_context), intent(in) :: context
    context_is_test_only = context%test_only .and. &
      has_test_prefix(context%run_id) .and. has_test_prefix(context%model_id) .and. &
      has_test_prefix(context%source_id) .and. has_test_prefix(context%input_id) .and. &
      has_test_prefix(context%dof_order_id) .and. context%rank > 0_int32 .and. &
      context%rpeat > 0_int32 .and. context%fem_iteration > 0_int32 .and. &
      context%fem_call_ordinal > 0_int32
  end function context_is_test_only

  logical function has_test_prefix(value)
    character(len=*), intent(in) :: value
    has_test_prefix = len_trim(value) > 10
    if (has_test_prefix) has_test_prefix = value(1:10) == 'TEST_ONLY:'
  end function has_test_prefix

  logical function valid_sha256_hex(value)
    character(len=*), intent(in) :: value
    integer :: k, code
    valid_sha256_hex = .false.
    if (len_trim(value) /= 64) return
    do k = 1, 64
      code = iachar(value(k:k))
      if (.not. ((code >= iachar('0') .and. code <= iachar('9')) .or. &
                 (code >= iachar('a') .and. code <= iachar('f')) .or. &
                 (code >= iachar('A') .and. code <= iachar('F')))) return
    end do
    valid_sha256_hex = .true.
  end function valid_sha256_hex

  subroutine signed_byte(value, byte_value)
    integer(int64), intent(in) :: value
    integer(int8), intent(out) :: byte_value
    integer(int64) :: low
    low = iand(value,255_int64)
    if (low >= 128_int64) low = low - 256_int64
    byte_value = int(low,int8)
  end subroutine signed_byte

  subroutine write_u32(unit,value,ios)
    integer, intent(in) :: unit
    integer(int32), intent(in) :: value
    integer, intent(out) :: ios
    integer :: k
    integer(int8) :: bytes(4)
    integer(int64) :: wide
    wide = iand(int(value,int64),int(z'FFFFFFFF',int64))
    do k = 0, 3
      call signed_byte(ishft(wide,-8*k),bytes(k+1))
    end do
    write(unit,iostat=ios) bytes
  end subroutine write_u32

  subroutine write_u64(unit,value,ios)
    integer, intent(in) :: unit
    integer(int64), intent(in) :: value
    integer, intent(out) :: ios
    integer :: k
    integer(int8) :: bytes(8)
    do k = 0, 7
      call signed_byte(ishft(value,-8*k),bytes(k+1))
    end do
    write(unit,iostat=ios) bytes
  end subroutine write_u64

end module r6_sparse_snapshot_writer
