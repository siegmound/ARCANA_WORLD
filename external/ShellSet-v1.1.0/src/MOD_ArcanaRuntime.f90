MODULE ArcanaRuntime
  USE, INTRINSIC :: IEEE_ARITHMETIC, ONLY: IEEE_IS_FINITE
  IMPLICIT NONE
  PRIVATE

  INTEGER, PARAMETER, PUBLIC :: ARCANA_NODE_COUNT = 64442
  INTEGER, PARAMETER, PUBLIC :: ARCANA_FIELD_COUNT = 51
  CHARACTER(LEN=*), PARAMETER, PUBLIC :: ARCANA_MODE = &
       'ARCANA_R6_PRE_ORBDATA_RUNTIME_V1'
  CHARACTER(LEN=*), PARAMETER, PUBLIC :: ARCANA_SCHEMA = &
       'arcana_worldsim.r6.shellset_owner_bound_runtime.v1'
  CHARACTER(LEN=*), PARAMETER, PUBLIC :: ARCANA_FEG_MARKER = &
       'ARCANA_R6_PRE_ORBDATA_RUNTIME_V1'

  INTEGER, PARAMETER :: I_NODE = 1, I_OWNER_ROW = 2, I_OWNER_COL = 3
  INTEGER, PARAMETER :: I_OWNER_DOMAIN = 4, I_DOMAIN_MASK = 5
  INTEGER, PARAMETER :: I_MIXED = 6, I_CLASS_PRESENT = 7, I_CLASS_ID = 8
  INTEGER, PARAMETER :: I_BRANCH = 9, I_AGE_PRESENT = 10, I_AGE = 11
  INTEGER, PARAMETER :: I_EFF_PRESENT = 12, I_EFF_AGE = 13
  INTEGER, PARAMETER :: I_SURFACE_T = 14, I_SURFACE_Q = 15
  INTEGER, PARAMETER :: I_CRUST = 16, I_MANTLE = 17, I_LAB = 18
  INTEGER, PARAMETER :: I_MOHO_T = 19, I_MOHO_Q = 20
  INTEGER, PARAMETER :: I_LAB_T = 21, I_LAB_Q = 22
  INTEGER, PARAMETER :: I_RATE_PRESENT = 23, I_RATE = 24
  INTEGER, PARAMETER :: I_MATERIAL_CONFIG = 25, I_CRUST_MATERIAL = 26
  INTEGER, PARAMETER :: I_MANTLE_MATERIAL = 27, I_CRUST_RHO = 28
  INTEGER, PARAMETER :: I_CRUST_K = 29, I_CRUST_ALPHA = 30
  INTEGER, PARAMETER :: I_CRUST_RADIO = 31, I_CRUST_CP = 32
  INTEGER, PARAMETER :: I_MANTLE_RHO = 33, I_MANTLE_K = 34
  INTEGER, PARAMETER :: I_MANTLE_ALPHA = 35, I_MANTLE_RADIO = 36
  INTEGER, PARAMETER :: I_MANTLE_CP = 37, I_RHO_ASTH = 38, I_RHO_WATER = 39
  INTEGER, PARAMETER :: I_L1_Z0 = 40, I_L1_Z1 = 41, I_L1_C3 = 42
  INTEGER, PARAMETER :: I_L1_C2 = 43, I_L1_C1 = 44, I_L1_C0 = 45
  INTEGER, PARAMETER :: I_L2_Z0 = 46, I_L2_Z1 = 47, I_L2_C3 = 48
  INTEGER, PARAMETER :: I_L2_C2 = 49, I_L2_C1 = 50, I_L2_C0 = 51

  REAL(KIND=8), PARAMETER :: TOL_T = 2.0D-7
  REAL(KIND=8), PARAMETER :: TOL_Q = 2.0D-12
  REAL(KIND=8), PARAMETER :: TOL_Z = 1.0D-8
  REAL(KIND=8), PARAMETER :: TOL_PROFILE = 1.0D-7
  REAL(KIND=8), PARAMETER :: TEMPERATURE_CEILING = 1900.0D0

  TYPE, PUBLIC :: ArcanaRuntimeNode
     REAL(KIND=8) :: value(ARCANA_FIELD_COUNT)
  END TYPE ArcanaRuntimeNode

  TYPE(ArcanaRuntimeNode), ALLOCATABLE, SAVE :: runtime_nodes(:)

  PUBLIC :: ArcanaRuntimeRead, ArcanaRuntimeGet, ArcanaRuntimeRelease

CONTAINS

  SUBROUTINE ArcanaRuntimeRead(unit_number, expected_nodes, ierr, message)
    INTEGER, INTENT(IN) :: unit_number, expected_nodes
    INTEGER, INTENT(OUT) :: ierr
    CHARACTER(LEN=*), INTENT(OUT) :: message
    CHARACTER(LEN=4096) :: line
    CHARACTER(LEN=128) :: tokens(ARCANA_FIELD_COUNT + 1)
    REAL(KIND=8) :: values(ARCANA_FIELD_COUNT)
    INTEGER :: ios, i, j, token_count, branch_count(3), mixed_count
    LOGICAL :: overflow

    ierr = 0
    message = ' '
    IF (ALLOCATED(runtime_nodes)) DEALLOCATE(runtime_nodes)
    IF (expected_nodes /= ARCANA_NODE_COUNT) THEN
       message = 'ARCANA_FEG_NODE_COUNT_MISMATCH'
       ierr = 1
       RETURN
    END IF
    ALLOCATE(runtime_nodes(ARCANA_NODE_COUNT), STAT=ios)
    IF (ios /= 0) THEN
       message = 'ARCANA_RUNTIME_ALLOCATION_FAILED'
       ierr = 1
       RETURN
    END IF
    branch_count = 0
    mixed_count = 0

    READ(unit_number, '(A)', IOSTAT=ios) line
    IF (ios /= 0) THEN
       message = 'ARCANA_RUNTIME_HEADER_MISSING'
       GOTO 900
    END IF
    CALL Tokenize(line, tokens, token_count, overflow)
    IF (overflow .OR. token_count /= 3) THEN
       message = 'ARCANA_RUNTIME_HEADER_MALFORMED'
       GOTO 900
    END IF
    IF (TRIM(tokens(1)) /= ARCANA_MODE) THEN
       message = 'ARCANA_RUNTIME_BAD_MAGIC'
       GOTO 900
    END IF
    IF (TRIM(tokens(2)) /= ARCANA_SCHEMA) THEN
       message = 'ARCANA_RUNTIME_BAD_SCHEMA'
       GOTO 900
    END IF
    IF (TRIM(tokens(3)) /= '64442') THEN
       message = 'ARCANA_RUNTIME_BAD_NODE_COUNT'
       GOTO 900
    END IF

    DO i = 1, ARCANA_NODE_COUNT
       READ(unit_number, '(A)', IOSTAT=ios) line
       IF (ios /= 0) THEN
          message = 'ARCANA_RUNTIME_RECORD_MISSING'
          GOTO 900
       END IF
       CALL Tokenize(line, tokens, token_count, overflow)
       IF (overflow .OR. token_count /= ARCANA_FIELD_COUNT) THEN
          message = 'ARCANA_RUNTIME_RECORD_FIELD_COUNT_INVALID'
          GOTO 900
       END IF
       DO j = 1, ARCANA_FIELD_COUNT
          IF (.NOT. IsNumericToken(TRIM(tokens(j)))) THEN
             message = 'ARCANA_RUNTIME_RECORD_TOKEN_INVALID'
             GOTO 900
          END IF
          READ(tokens(j), *, IOSTAT=ios) values(j)
          IF (ios /= 0) THEN
             message = 'ARCANA_RUNTIME_RECORD_NUMBER_INVALID'
             GOTO 900
          END IF
          IF (.NOT. IEEE_IS_FINITE(values(j))) THEN
             message = 'ARCANA_RUNTIME_RECORD_NONFINITE'
             GOTO 900
          END IF
       END DO
       CALL ValidateRecord(values, i, message)
       IF (LEN_TRIM(message) /= 0) GOTO 900
       branch_count(INT(values(I_BRANCH))) = branch_count(INT(values(I_BRANCH))) + 1
       IF (values(I_MIXED) == 1.0D0) mixed_count = mixed_count + 1
       runtime_nodes(i)%value = values
    END DO

    IF (ANY(branch_count /= (/14258,108,50076/)) .OR. mixed_count /= 2697) THEN
       message = 'ARCANA_RUNTIME_GOVERNED_RECORD_COUNTS_MISMATCH'
       GOTO 900
    END IF

    READ(unit_number, '(A)', IOSTAT=ios) line
    IF (ios >= 0) THEN
       message = 'ARCANA_RUNTIME_TRAILING_RECORD_OR_DATA'
       GOTO 900
    END IF
    RETURN

900 CONTINUE
    ierr = 1
    IF (ALLOCATED(runtime_nodes)) DEALLOCATE(runtime_nodes)
  END SUBROUTINE ArcanaRuntimeRead

  SUBROUTINE ArcanaRuntimeGet(node_id, values, ierr)
    INTEGER, INTENT(IN) :: node_id
    REAL(KIND=8), INTENT(OUT) :: values(ARCANA_FIELD_COUNT)
    INTEGER, INTENT(OUT) :: ierr
    ierr = 1
    IF (.NOT. ALLOCATED(runtime_nodes)) RETURN
    IF (node_id < 1 .OR. node_id > ARCANA_NODE_COUNT) RETURN
    IF (INT(runtime_nodes(node_id)%value(I_NODE)) /= node_id) RETURN
    values = runtime_nodes(node_id)%value
    ierr = 0
  END SUBROUTINE ArcanaRuntimeGet

  SUBROUTINE ArcanaRuntimeRelease()
    IF (ALLOCATED(runtime_nodes)) DEALLOCATE(runtime_nodes)
  END SUBROUTINE ArcanaRuntimeRelease

  SUBROUTINE Tokenize(line, tokens, count, overflow)
    CHARACTER(LEN=*), INTENT(IN) :: line
    CHARACTER(LEN=*), INTENT(OUT) :: tokens(:)
    INTEGER, INTENT(OUT) :: count
    LOGICAL, INTENT(OUT) :: overflow
    INTEGER :: i, first, last, n
    CHARACTER :: ch

    tokens = ' '
    count = 0
    overflow = .FALSE.
    n = LEN_TRIM(line)
    i = 1
    DO WHILE (i <= n)
       ch = line(i:i)
       IF (ch == ' ' .OR. ch == ACHAR(9)) THEN
          i = i + 1
          CYCLE
       END IF
       first = i
       DO WHILE (i <= n)
          ch = line(i:i)
          IF (ch == ' ' .OR. ch == ACHAR(9)) EXIT
          i = i + 1
       END DO
       last = i - 1
       count = count + 1
       IF (count > SIZE(tokens)) THEN
          overflow = .TRUE.
          RETURN
       END IF
       IF (last - first + 1 > LEN(tokens)) THEN
          overflow = .TRUE.
          RETURN
       END IF
       tokens(count) = line(first:last)
    END DO
  END SUBROUTINE Tokenize

  LOGICAL FUNCTION IsNumericToken(token)
    CHARACTER(LEN=*), INTENT(IN) :: token
    INTEGER :: i
    CHARACTER :: ch
    IsNumericToken = LEN_TRIM(token) > 0
    DO i = 1, LEN_TRIM(token)
       ch = token(i:i)
       IF (INDEX('0123456789+-.eEdD', ch) == 0) THEN
          IsNumericToken = .FALSE.
          RETURN
       END IF
    END DO
  END FUNCTION IsNumericToken

  LOGICAL FUNCTION IsIntegerInRange(value, lower, upper)
    REAL(KIND=8), INTENT(IN) :: value
    INTEGER, INTENT(IN) :: lower, upper
    IsIntegerInRange = .FALSE.
    IF (value < REAL(lower,8) .OR. value > REAL(upper,8)) RETURN
    IsIntegerInRange = value == ANINT(value)
  END FUNCTION IsIntegerInRange

  SUBROUTINE ValidateRecord(v, expected_id, message)
    REAL(KIND=8), INTENT(IN) :: v(ARCANA_FIELD_COUNT)
    INTEGER, INTENT(IN) :: expected_id
    CHARACTER(LEN=*), INTENT(OUT) :: message
    INTEGER :: branch, domain, mask, bit_count, bit_index
    REAL(KIND=8) :: lab_expected, t0, t1, q0, q1, temperature_max
    REAL(KIND=8) :: xlen, min_gradient

    message = ' '
    IF (.NOT. IsIntegerInRange(v(I_NODE), expected_id, expected_id)) THEN
       message = 'ARCANA_RUNTIME_NODE_ID_ORDER_OR_DUPLICATE'
       RETURN
    END IF
    IF (.NOT. IsIntegerInRange(v(I_OWNER_ROW), 0, 179) .OR. &
        .NOT. IsIntegerInRange(v(I_OWNER_COL), 0, 358) .OR. &
        .NOT. IsIntegerInRange(v(I_OWNER_DOMAIN), 1, 6) .OR. &
        .NOT. IsIntegerInRange(v(I_DOMAIN_MASK), 1, 63) .OR. &
        .NOT. IsIntegerInRange(v(I_MIXED), 0, 1) .OR. &
        .NOT. IsIntegerInRange(v(I_CLASS_PRESENT), 0, 1) .OR. &
        .NOT. IsIntegerInRange(v(I_CLASS_ID), 0, 3) .OR. &
        .NOT. IsIntegerInRange(v(I_BRANCH), 1, 3) .OR. &
        .NOT. IsIntegerInRange(v(I_AGE_PRESENT), 0, 1) .OR. &
        .NOT. IsIntegerInRange(v(I_EFF_PRESENT), 0, 1) .OR. &
        .NOT. IsIntegerInRange(v(I_RATE_PRESENT), 0, 1)) THEN
       message = 'ARCANA_RUNTIME_IDENTITY_OR_FLAG_INVALID'
       RETURN
    END IF
    domain = INT(v(I_OWNER_DOMAIN))
    mask = INT(v(I_DOMAIN_MASK))
    IF (.NOT. BTEST(mask, domain - 1)) THEN
       message = 'ARCANA_RUNTIME_OWNER_DOMAIN_NOT_IN_SUPPORT'
       RETURN
    END IF
    bit_count = 0
    DO bit_index = 0, 5
       IF (BTEST(mask, bit_index)) bit_count = bit_count + 1
    END DO
    IF (INT(v(I_MIXED)) /= MERGE(1, 0, bit_count > 1)) THEN
       message = 'ARCANA_RUNTIME_MIXED_SUPPORT_FLAG_INVALID'
       RETURN
    END IF

    branch = INT(v(I_BRANCH))
    IF (v(I_MATERIAL_CONFIG) /= 1.0D0 .OR. &
        .NOT. IsIntegerInRange(v(I_CRUST_MATERIAL), 1, 2) .OR. &
        v(I_MANTLE_MATERIAL) /= 1.0D0) THEN
       message = 'ARCANA_RUNTIME_MATERIAL_BINDING_INVALID'
       RETURN
    END IF
    IF (MIN(v(I_CRUST_RHO), v(I_CRUST_K), v(I_CRUST_CP), &
            v(I_MANTLE_RHO), v(I_MANTLE_K), v(I_MANTLE_CP), &
            v(I_RHO_ASTH), v(I_RHO_WATER)) <= 0.0D0 .OR. &
        v(I_CRUST_ALPHA) <= 0.0D0 .OR. v(I_MANTLE_ALPHA) <= 0.0D0 .OR. &
        v(I_CRUST_RADIO) < 0.0D0 .OR. v(I_MANTLE_RADIO) < 0.0D0) THEN
       message = 'ARCANA_RUNTIME_MATERIAL_VALUE_INVALID'
       RETURN
    END IF
    IF (v(I_SURFACE_Q) <= 0.0D0 .OR. v(I_CRUST) <= 0.0D0 .OR. &
        v(I_MANTLE) <= 0.0D0 .OR. v(I_LAB) <= v(I_CRUST)) THEN
       message = 'ARCANA_RUNTIME_GOVERNED_GEOMETRY_OR_Q_INVALID'
       RETURN
    END IF
    lab_expected = v(I_CRUST) + v(I_MANTLE)
    IF (ABS(v(I_LAB) - lab_expected) > TOL_Z) THEN
       message = 'ARCANA_RUNTIME_LAB_GEOMETRY_MISMATCH'
       RETURN
    END IF

    IF (branch == 1) THEN
       IF (domain == 1 .OR. v(I_CLASS_PRESENT) /= 1.0D0 .OR. &
           .NOT. IsIntegerInRange(v(I_CLASS_ID), 1, 3) .OR. &
           v(I_AGE_PRESENT) /= 0.0D0 .OR. v(I_AGE) /= 0.0D0 .OR. &
           v(I_EFF_PRESENT) /= 0.0D0 .OR. v(I_EFF_AGE) /= 0.0D0 .OR. &
           v(I_RATE_PRESENT) /= 1.0D0 .OR. &
           v(I_CRUST_MATERIAL) /= 1.0D0) THEN
          message = 'ARCANA_RUNTIME_CONTINENTAL_BRANCH_STATE_INVALID'
          RETURN
       END IF
    ELSE IF (branch == 2) THEN
       IF (domain /= 1 .OR. v(I_CLASS_PRESENT) /= 0.0D0 .OR. &
           v(I_CLASS_ID) /= 0.0D0 .OR. v(I_AGE_PRESENT) /= 1.0D0 .OR. &
           v(I_AGE) /= 0.0D0 .OR. v(I_EFF_PRESENT) /= 1.0D0 .OR. &
           v(I_EFF_AGE) <= 0.0D0 .OR. v(I_RATE_PRESENT) /= 0.0D0 .OR. &
           v(I_RATE) /= 0.0D0 .OR. v(I_SURFACE_Q) /= 0.300D0 .OR. &
           v(I_CRUST_MATERIAL) /= 2.0D0) THEN
          message = 'ARCANA_RUNTIME_RIDGE_STATE_INVALID'
          RETURN
       END IF
    ELSE
       IF (domain /= 1 .OR. v(I_CLASS_PRESENT) /= 0.0D0 .OR. &
           v(I_CLASS_ID) /= 0.0D0 .OR. v(I_AGE_PRESENT) /= 1.0D0 .OR. &
           v(I_AGE) <= 0.0D0 .OR. v(I_EFF_PRESENT) /= 0.0D0 .OR. &
           v(I_EFF_AGE) /= 0.0D0 .OR. v(I_RATE_PRESENT) /= 0.0D0 .OR. &
           v(I_RATE) /= 0.0D0 .OR. v(I_CRUST_MATERIAL) /= 2.0D0) THEN
          message = 'ARCANA_RUNTIME_POSITIVE_OCEAN_STATE_INVALID'
          RETURN
       END IF
    END IF

    IF (ABS(v(I_L1_Z0)) > TOL_Z .OR. &
        ABS(v(I_L1_Z1) - v(I_CRUST)) > TOL_Z .OR. &
        ABS(v(I_L2_Z0) - v(I_CRUST)) > TOL_Z .OR. &
        ABS(v(I_L2_Z1) - v(I_LAB)) > TOL_Z) THEN
       message = 'ARCANA_RUNTIME_PROFILE_GEOMETRY_INVALID'
       RETURN
    END IF
    xlen = v(I_L1_Z1) - v(I_L1_Z0)
    CALL ValidatePolynomial(v(I_L1_C3), v(I_L1_C2), v(I_L1_C1), &
         v(I_L1_C0), xlen, temperature_max, min_gradient)
    IF (min_gradient < -1.0D-12 .OR. &
        temperature_max >= TEMPERATURE_CEILING) THEN
       message = 'ARCANA_RUNTIME_LAYER1_PROFILE_INVALID_OR_OVER_CEILING'
       RETURN
    END IF
    t0 = Polynomial(v(I_L1_C3), v(I_L1_C2), v(I_L1_C1), &
         v(I_L1_C0), 0.0D0)
    t1 = Polynomial(v(I_L1_C3), v(I_L1_C2), v(I_L1_C1), &
         v(I_L1_C0), xlen)
    q0 = v(I_CRUST_K) * Derivative(v(I_L1_C3), v(I_L1_C2), &
         v(I_L1_C1), xlen, 0.0D0)
    q1 = v(I_CRUST_K) * Derivative(v(I_L1_C3), v(I_L1_C2), &
         v(I_L1_C1), xlen, xlen)
    IF (ABS(t0 - v(I_SURFACE_T)) > TOL_T .OR. &
        ABS(q0 - v(I_SURFACE_Q)) > TOL_Q .OR. &
        ABS(t1 - v(I_MOHO_T)) > TOL_T .OR. &
        ABS(q1 - v(I_MOHO_Q)) > TOL_Q) THEN
       message = 'ARCANA_RUNTIME_LAYER1_BOUNDARY_MISMATCH'
       RETURN
    END IF

    xlen = v(I_L2_Z1) - v(I_L2_Z0)
    CALL ValidatePolynomial(v(I_L2_C3), v(I_L2_C2), v(I_L2_C1), &
         v(I_L2_C0), xlen, temperature_max, min_gradient)
    IF (min_gradient < -1.0D-12 .OR. &
        temperature_max >= TEMPERATURE_CEILING) THEN
       message = 'ARCANA_RUNTIME_LAYER2_PROFILE_INVALID_OR_OVER_CEILING'
       RETURN
    END IF
    t0 = Polynomial(v(I_L2_C3), v(I_L2_C2), v(I_L2_C1), &
         v(I_L2_C0), 0.0D0)
    t1 = Polynomial(v(I_L2_C3), v(I_L2_C2), v(I_L2_C1), &
         v(I_L2_C0), xlen)
    q0 = v(I_MANTLE_K) * Derivative(v(I_L2_C3), v(I_L2_C2), &
         v(I_L2_C1), xlen, 0.0D0)
    q1 = v(I_MANTLE_K) * Derivative(v(I_L2_C3), v(I_L2_C2), &
         v(I_L2_C1), xlen, xlen)
    IF (ABS(t0 - v(I_MOHO_T)) > TOL_T .OR. &
        ABS(q0 - v(I_MOHO_Q)) > TOL_Q .OR. &
        ABS(t1 - v(I_LAB_T)) > TOL_T .OR. &
        ABS(q1 - v(I_LAB_Q)) > TOL_Q) THEN
       message = 'ARCANA_RUNTIME_LAYER2_BOUNDARY_MISMATCH'
       RETURN
    END IF
  END SUBROUTINE ValidateRecord

  REAL(KIND=8) FUNCTION Polynomial(c3, c2, c1, c0, x)
    REAL(KIND=8), INTENT(IN) :: c3, c2, c1, c0, x
    Polynomial = ((c3*x + c2)*x + c1)*x + c0
  END FUNCTION Polynomial

  REAL(KIND=8) FUNCTION Derivative(c3, c2, c1, length, x)
    REAL(KIND=8), INTENT(IN) :: c3, c2, c1, length, x
    Derivative = (3.0D0*c3*x + 2.0D0*c2)*x + c1
  END FUNCTION Derivative

  SUBROUTINE ValidatePolynomial(c3, c2, c1, c0, length, max_temperature, min_derivative)
    REAL(KIND=8), INTENT(IN) :: c3, c2, c1, c0, length
    REAL(KIND=8), INTENT(OUT) :: max_temperature, min_derivative
    REAL(KIND=8) :: disc, a, b, c, root1, root2, vertex, value
    REAL(KIND=8) :: t_start, t_end
    INTEGER :: nroot

    t_start = Polynomial(c3,c2,c1,c0,0.0D0)
    t_end = Polynomial(c3,c2,c1,c0,length)
    max_temperature = MAX(t_start,t_end)
    min_derivative = MIN(Derivative(c3,c2,c1,length,0.0D0), &
         Derivative(c3,c2,c1,length,length))
    a = 3.0D0*c3
    b = 2.0D0*c2
    c = c1
    nroot = 0
    IF (ABS(a) < 1.0D-300) THEN
       IF (ABS(b) >= 1.0D-300) THEN
          root1 = -c/b
          IF (root1 > 0.0D0 .AND. root1 < length) THEN
             nroot = 1
             CALL IncludeStationary(root1,c3,c2,c1,c0,max_temperature)
          END IF
       END IF
    ELSE
       disc = b*b - 4.0D0*a*c
       IF (disc >= 0.0D0) THEN
          root1 = (-b-SQRT(disc))/(2.0D0*a)
          root2 = (-b+SQRT(disc))/(2.0D0*a)
          IF (root1 > 0.0D0 .AND. root1 < length) THEN
             nroot = nroot + 1
             CALL IncludeStationary(root1,c3,c2,c1,c0,max_temperature)
          END IF
          IF (root2 > 0.0D0 .AND. root2 < length) THEN
             nroot = nroot + 1
             CALL IncludeStationary(root2,c3,c2,c1,c0,max_temperature)
          END IF
       END IF
       IF (a > 0.0D0) THEN
          vertex = -b/(2.0D0*a)
          IF (vertex > 0.0D0 .AND. vertex < length) THEN
             value = Derivative(c3,c2,c1,length,vertex)
             min_derivative = MIN(min_derivative,value)
          END IF
       END IF
    END IF
    IF (nroot > 0) THEN
       max_temperature = MAX(max_temperature,t_start,t_end)
    END IF
  END SUBROUTINE ValidatePolynomial

  SUBROUTINE IncludeStationary(x,c3,c2,c1,c0,max_temperature)
    REAL(KIND=8), INTENT(IN) :: x,c3,c2,c1,c0
    REAL(KIND=8), INTENT(INOUT) :: max_temperature
    max_temperature = MAX(max_temperature,Polynomial(c3,c2,c1,c0,x))
  END SUBROUTINE IncludeStationary

END MODULE ArcanaRuntime
