! Synthetic cross-language fixture for ARCANA_SPARSE_A0_B0_SNAPSHOT_V1.
! This program is not linked to ShellSet and never calls a solver.
module n2b_snapshot_fixture
  use iso_fortran_env, only: int8, int32, int64, real64, iostat_end
  use ieee_arithmetic, only: ieee_is_finite, ieee_support_datatype
  implicit none
  private
  public :: run_fixture
  character(len=8), parameter :: magic = 'ARCNSNP1'
  integer(int32), parameter :: n = 4, kl = 1, ku = 2
  integer(int32), parameter :: expected_count = 12
contains
  subroutine run_fixture()
    character(len=8) :: mode
    character(len=1024) :: path
    character(len=64) :: expected_digest
    character(len=1024) :: count_text
    integer :: argc, ios, expected_records
    argc = command_argument_count()
    if (argc < 3) error stop 21
    call get_command_argument(1, mode)
    call get_command_argument(2, path)
    call get_command_argument(3, expected_digest)
    if (len_trim(expected_digest) /= 64) error stop 22
    if (.not. ieee_support_datatype(0.0_real64)) error stop 23
    if (storage_size(0.0_real64) /= 64) error stop 24
    select case (trim(mode))
    case ('write')
      call write_fixture(trim(path), trim(expected_digest))
    case ('read')
      if (argc /= 4) error stop 25
      call get_command_argument(4, count_text)
      read(count_text, *, iostat=ios) expected_records
      if (ios /= 0) error stop 26
      call read_fixture(trim(path), trim(expected_digest), expected_records)
    case default
      error stop 27
    end select
  end subroutine run_fixture

  subroutine fixture_values(a, b)
    real(real64), intent(out) :: a(n,n), b(n)
    integer(int64) :: bits
    a = 0.0_real64
    a(1,1)=4.0_real64; a(1,2)=1.0_real64
    bits = int(z'8000000000000000', int64)
    a(1,3)=transfer(bits, 0.0_real64) ! explicit negative zero
    a(2,1)=2.0_real64; a(2,2)=5.0_real64
    a(2,3)=3.0_real64; a(2,4)=7.0_real64
    bits = 1_int64
    a(3,2)=transfer(bits, 0.0_real64) ! smallest binary64 subnormal
    a(3,3)=6.0_real64; a(3,4)=4.0_real64
    a(4,3)=1.0_real64; a(4,4)=3.0_real64
    b = [8.0_real64, 10.0_real64, -7.0_real64, 1.0_real64]
  end subroutine fixture_values

  subroutine to_i8(unsigned_value, value)
    integer(int64), intent(in) :: unsigned_value
    integer(int8), intent(out) :: value
    integer(int64) :: byte_value
    byte_value = iand(unsigned_value, 255_int64)
    if (byte_value >= 128_int64) byte_value = byte_value - 256_int64
    value = int(byte_value, int8)
  end subroutine to_i8

  subroutine write_u32(unit, value)
    integer, intent(in) :: unit
    integer(int32), intent(in) :: value
    integer :: k
    integer(int8) :: byte_value
    integer(int64) :: wide
    wide = iand(int(value, int64), int(z'FFFFFFFF', int64))
    do k=0,3
      call to_i8(ishft(wide, -8*k), byte_value)
      write(unit) byte_value
    end do
  end subroutine write_u32

  subroutine write_u64(unit, value)
    integer, intent(in) :: unit
    integer(int64), intent(in) :: value
    integer :: k
    integer(int8) :: byte_value
    do k=0,7
      call to_i8(ishft(value, -8*k), byte_value)
      write(unit) byte_value
    end do
  end subroutine write_u64

  subroutine write_digest(unit, hex_digest)
    integer, intent(in) :: unit
    character(len=*), intent(in) :: hex_digest
    integer :: k, ios, value
    integer(int8) :: byte_value
    do k=1,64,2
      read(hex_digest(k:k+1), '(Z2)', iostat=ios) value
      if (ios /= 0) error stop 31
      call to_i8(int(value,int64), byte_value)
      write(unit) byte_value
    end do
  end subroutine write_digest

  subroutine read_byte(unit, value, ios)
    integer, intent(in) :: unit
    integer(int8), intent(out) :: value
    integer, intent(out) :: ios
    read(unit, iostat=ios) value
  end subroutine read_byte

  subroutine read_u32(unit, value, ios)
    integer, intent(in) :: unit
    integer(int64), intent(out) :: value
    integer, intent(out) :: ios
    integer :: k
    integer(int8) :: byte_value
    value=0_int64
    do k=0,3
      call read_byte(unit, byte_value, ios)
      if (ios /= 0) return
      value=ior(value, shiftl(int(iand(int(byte_value,int32),255_int32),int64),8*k))
    end do
  end subroutine read_u32

  subroutine read_u64(unit, value, ios)
    integer, intent(in) :: unit
    integer(int64), intent(out) :: value
    integer, intent(out) :: ios
    integer :: k
    integer(int8) :: byte_value
    value=0_int64
    do k=0,7
      call read_byte(unit, byte_value, ios)
      if (ios /= 0) return
      value=ior(value, shiftl(int(iand(int(byte_value,int32),255_int32),int64),8*k))
    end do
  end subroutine read_u64

  subroutine read_digest(unit, hex_digest, ios)
    integer, intent(in) :: unit
    character(len=64), intent(out) :: hex_digest
    integer, intent(out) :: ios
    integer :: k, unsigned_value
    integer(int8) :: byte_value
    character(len=2) :: pair
    hex_digest=''
    do k=1,32
      call read_byte(unit, byte_value, ios)
      if (ios /= 0) return
      unsigned_value=iand(int(byte_value,int32),255_int32)
      write(pair,'(Z2.2)') unsigned_value
      hex_digest(2*k-1:2*k)=pair
    end do
  end subroutine read_digest

  subroutine write_fixture(path, source_digest)
    character(len=*), intent(in) :: path, source_digest
    integer :: unit, i, j, ios
    integer(int32) :: count
    integer(int64) :: bits
    real(real64) :: a(n,n), b(n)
    call fixture_values(a,b)
    count=0_int32
    do i=1,n
      do j=max(1,i-kl),min(n,i+ku)
        bits=transfer(a(i,j),bits)
        if (bits /= 0_int64) count=count+1_int32
      end do
    end do
    if (count /= expected_count) error stop 32
    open(newunit=unit,file=path,status='replace',access='stream',form='unformatted',iostat=ios)
    if (ios /= 0) error stop 33
    write(unit) magic
    call write_u32(unit,n); call write_u32(unit,kl); call write_u32(unit,ku)
    call write_u32(unit,count); call write_digest(unit,source_digest)
    do i=1,n
      do j=max(1,i-kl),min(n,i+ku)
        bits=transfer(a(i,j),bits)
        if (bits /= 0_int64) then
          call write_u32(unit,int(i-1,int32)); call write_u32(unit,int(j-1,int32))
          call write_u64(unit,bits)
        end if
      end do
    end do
    do i=1,n
      bits=transfer(b(i),bits); call write_u64(unit,bits)
    end do
    close(unit)
  end subroutine write_fixture

  subroutine read_fixture(path, expected_digest, expected_records)
    character(len=*), intent(in) :: path, expected_digest
    integer, intent(in) :: expected_records
    integer :: unit, ios, i, j, k, count
    integer(int64) :: value, ri, cj
    integer(int64) :: previous_i, previous_j
    integer(int8) :: byte_value
    character(len=8) :: file_magic
    character(len=64) :: source_digest
    real(real64) :: a(n,n), b(n), coefficient
    integer(int64) :: bits
    logical :: seen(n,n)
    character(len=1024) :: raw_path
    integer :: raw_unit
    a=0.0_real64; b=0.0_real64; seen=.false.
    open(newunit=unit,file=path,status='old',access='stream',form='unformatted',iostat=ios)
    if (ios /= 0) error stop 41
    file_magic=''
    read(unit,iostat=ios) file_magic
    if (ios /= 0 .or. file_magic /= magic) error stop 42
    call read_u32(unit,value,ios); if (ios /= 0 .or. value /= n) error stop 43
    call read_u32(unit,value,ios); if (ios /= 0 .or. value /= kl) error stop 44
    call read_u32(unit,value,ios); if (ios /= 0 .or. value /= ku) error stop 45
    call read_u32(unit,value,ios); if (ios /= 0) error stop 46
    if (value /= int(expected_records,int64) .or. value /= int(expected_count,int64)) error stop 47
    count=int(value)
    call read_digest(unit,source_digest,ios)
    if (ios /= 0 .or. source_digest /= expected_digest) error stop 48
    previous_i=-1_int64; previous_j=-1_int64
    do k=1,count
      call read_u32(unit,ri,ios); if (ios /= 0) error stop 49
      call read_u32(unit,cj,ios); if (ios /= 0) error stop 50
      call read_u64(unit,bits,ios); if (ios /= 0) error stop 51
      if (ri >= n .or. cj >= n) error stop 52
      i=int(ri)+1; j=int(cj)+1
      if (i-j < -ku .or. i-j > kl) error stop 53
      if (seen(i,j)) error stop 54
      if (bits == 0_int64) error stop 55
      coefficient=transfer(bits,coefficient)
      if (.not. ieee_is_finite(coefficient)) error stop 56
      if (ri < previous_i .or. (ri == previous_i .and. cj <= previous_j)) error stop 61
      a(i,j)=coefficient; seen(i,j)=.true.
      previous_i=ri; previous_j=cj
    end do
    do i=1,n
      call read_u64(unit,bits,ios); if (ios /= 0) error stop 57
      b(i)=transfer(bits,b(i))
      if (.not. ieee_is_finite(b(i))) error stop 58
    end do
    call read_byte(unit,byte_value,ios)
    if (ios /= iostat_end) error stop 59
    close(unit)
    raw_path=trim(path)//'.raw'
    open(newunit=raw_unit,file=trim(raw_path),status='replace',access='stream',form='unformatted',iostat=ios)
    if (ios /= 0) error stop 60
    do i=1,n
      do j=max(1,i-kl),min(n,i+ku)
        bits=transfer(a(i,j),bits); call write_u64(raw_unit,bits)
      end do
    end do
    do i=1,n
      bits=transfer(b(i),bits); call write_u64(raw_unit,bits)
    end do
    close(raw_unit)
  end subroutine read_fixture
end module n2b_snapshot_fixture

program r6_si1_bandwidth_f2b_n2b_interop
  use n2b_snapshot_fixture, only: run_fixture
  implicit none
  call run_fixture()
end program r6_si1_bandwidth_f2b_n2b_interop
