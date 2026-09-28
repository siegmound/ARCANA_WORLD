# R6 PRE_ORBDATA heat-flow source audit

**Decision:** `R6_PRE_ORBDATA_HEAT_FLOW_SOURCE_AUDIT_SOURCE_EXTRACTED_PENDING_ADJUDICATION`

This is source evidence extraction only. It does not choose values, run OrbData/SHELLS, or close the PRE_ORBDATA gate.

## Qualified source identity

- Branch: `arcana-r6-runtime-capacity`
- Commit: `62fd474f229b2676fd9d39c5def45137d22d2481`
- Expected executable SHA-256 (identity reference; executable not read): `4c0044fe4332184d63408960a2237d4edb7da891b71f74b82bd1d5a83b27e918`
- Governed patch SHA-256: `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`
- Source-file authority: `GIT_TRACKED_FILES_ONLY` via `git ls-files -z`; tracked text files scanned: 30; untracked files scanned: false
- Content source: `verified HEAD blobs via git show HEAD:<tracked-path>`

## Evidence category scaffold

No source symbol is automatically assigned to a category; the initial item list remains unresolved until contextual source and parameter binding are reviewed.

| Evidence category | Supported context | Symbol assignments |
|---|---|---|
| `WORLD_HISTORY_PHYSICAL_INPUT` | ARCANA requires surface heat flow or an authorized source with provenance; current candidate manifest has no bound heat-flow artifact. The oceanic age field is an ARCANA physical input only on its governed ocean support; halo extension does not create authority. | None |
| `SPECIALIST_MODEL_CONFIGURATION` | The current thermomechanical contract places alphaT, conductivity, surface/reference temperatures, temperature limits, and geotherm controls in specialist configuration; values remain unset. | None |
| `NUMERICAL_GUARD_OR_LIMIT` | Pending source adjudication | None |
| `DERIVED_ORBDATA_STATE` | The governed ARCANA patch passes nodal heat-flow state through Assign as INOUT and writes it back; exact qualified-source precedence awaits extraction. | None |
| `UNRESOLVED_PENDING_SOURCE_ADJUDICATION` | Pending source adjudication | heatFl, dQdTdA, needQ, qArray, qLim0, dQL_dE, qLim1, ageMa, alphaT, conduc, TSurf, temLim, TAsthK, TADIAB, GRADIE, ZBASTH, delta_rho_limit |

## Required excerpts

### `heatFl`

`src/MOD_Data.f90:223`
```text
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                    TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                    elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                    thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                    arcanaMode,arcanaOcean,requestedTotalLithosphere, &
     &                    ModNum)
```

`src/MOD_Data.f90:272`
```text
       INTEGER, INTENT(IN) ::    nAX,    nAY,    nCX,    nCY,    nEX,    nEY, &
                            & iUnitL, iUnitT, &
                            &    nQX,    nQY,    nSX,    nSY
        REAL*8, INTENT(INOUT) :: elevat, heatFl
        REAL*8, INTENT(OUT) :: thickC, thickM, chemical_delta_rho, cooling_curvature
        LOGICAL, INTENT(IN) :: arcanaMode,arcanaOcean
        REAL*8, INTENT(IN) :: requestedTotalLithosphere
```

`src/MOD_Data.f90:381`
```text

!   Determine heat-flow, in needed:

       needQ = (heatFl == 0.0D0)
       IF (needQ) THEN
            ir1 = ((qY2 - pLat) / qDY) + 1.00001D0 ! truncated to INTEGER
            ir1 = MAX(ir1, 1)
```

`src/MOD_Data.f90:416`
```text
            fc = MIN(1.0D0, MAX(0.0D0, fc))
            top = qArray(ir1, ic1) + fc * (qArray(ir1, ic2) - qArray(ir1, ic1))
            bot = qArray(ir2, ic1) + fc * (qArray(ir2, ic2) - qArray(ir2, ic1))
            heatFl = top + fr * (bot - top)

!           Check for seafloor-age overriding heat-flow grid value:

```

`src/MOD_Data.f90:424`
```text
     &          ((.NOT. arcanaMode) .AND. ageMa < 200.0D0)) THEN
!              Seafloor age is valid (not "unknown" or "continental")
                 IF (ageMa <= 0.0D0) THEN
                      heatFl = qLim1
                 ELSE
!                     Carol A. Stein & Seth Stein [1992]
!                     A model for the global variation in oceanic
```

`src/MOD_Data.f90:432`
```text
!                     Nature, v. 359, 10 September, p. 123-129.
!                     According to their preferred GDH1 model:
                      IF (ageMa <= 55.0D0) THEN
                           heatFl = 0.510D0 / SQRT(ageMa)
                      ELSE
                           heatFl = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
                      END IF
```

`src/MOD_Data.f90:434`
```text
                      IF (ageMa <= 55.0D0) THEN
                           heatFl = 0.510D0 / SQRT(ageMa)
                      ELSE
                           heatFl = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
                      END IF
                 END IF
            END IF
```

`src/MOD_Data.f90:444`
```text
!  Apply limits on Q:

       qLimit = qLim0 + dQL_dE * elevat
       heatFl = MAX(heatFl, qLimit)
       heatFl = MIN(heatFl, qLim1)

!  Obtain crustal thickness from grid cArray:
```

`src/MOD_Data.f90:445`
```text

       qLimit = qLim0 + dQL_dE * elevat
       heatFl = MAX(heatFl, qLimit)
       heatFl = MIN(heatFl, qLim1)

!  Obtain crustal thickness from grid cArray:

```

`src/MOD_Data.f90:609`
```text
!   Compute steady-state GEOTHerm, as in old OrbData:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = -radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
```

`src/MOD_Data.f90:614`
```text
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1)
       geoth6 = qRed / conduc(2)
       geoth7 = -radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0
```

`src/MOD_Data.f90:629`
```text
       IF (test > TAsthK) THEN
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
```

`src/MOD_Data.f90:631`
```text
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
```

`src/MOD_Data.f90:632`
```text
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
```

`src/MOD_Data.f90:633`
```text
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
            qRed = heatFl - thickC * radio(1)
```

`src/MOD_Data.f90:636`
```text
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
            qRed = heatFl - thickC * radio(1)
            geoth6 = qRed / conduc(2)
       END IF

```

`src/MOD_Data.f90:658`
```text

       IF (cooling_curvature > 0.0D0) THEN
            t_geoth1 = TSurf
            t_geoth2 = heatFl / conduc(1)
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
```

`src/MOD_Data.f90:662`
```text
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
            t_qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
            t_geoth6 = qRed / conduc(2)
            t_geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))

```

`src/MOD_Data.f90:692`
```text
!   Build geotherm again with final cooling_curvature:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
```

`src/MOD_Data.f90:697`
```text
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
       geoth6 = qRed / conduc(2)
       geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0
```

`src/MOD_Shells.f90:3857`
```text
!   Decide which points are "continental"
!     (a distinction that matters only if iConve=4),
!     using zMoho as temporary storage for interpolated elevation,
!     and tLInt as temporary storage for interpolated heatflow:

CALL Interp (elev, mxEl, mxNode, nodes, numEl, & ! input
&              zMoho)                              ! output
```

`src/OrbData5.f90:49`
```text
real*8 :: offset,xNode,yNode,area,detJ,dXs,dYs,dXSP,dYSP,fLen,fpflt,fpsfer,fArg,sita
real*8 :: eX1,eX2,eDX,eY1,eY2,eDY
real*8 :: qX1,qX2,qDX,qY1,qY2,qDY,qLimit,aX1,aX2,aDX,aY1,aY2,aDY
real*8 :: cX1,cX2,cDX,cY1,cY2,cDY,sX1,sX2,sDX,sY1,sY2,sDY,pLon,pLat,elevat,heatFl
real*8 :: domainX1,domainX2,domainDX,domainY1,domainY2,domainDY
real*8 :: lithoX1,lithoX2,lithoDX,lithoY1,lithoY2,lithoDY
real*8 :: requestedTotalLithosphere,arcLon,arcFr,arcFc,arcTop,arcBot,domainValue
```

`src/OrbData5.f90:484`
```text
            pLon = yNode(iNode) * 57.2957795130823D0
            pLat = 90.0D0 - xNode(iNode) * 57.2957795130823D0
            elevat = elev(iNode)
            heatFl = dQdTdA(iNode)

            arcanaOcean=.FALSE.
            requestedTotalLithosphere=0.0D0
```

`src/OrbData5.f90:540`
```text
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                   TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                   elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                   thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                   arcanaMode,arcanaOcean,requestedTotalLithosphere, &
     &                   ModNum)
```

`src/OrbData5.f90:546`
```text
     &                   ModNum)

            elev(iNode) = elevat
            dQdTdA(iNode) = heatFl
            zMNode(iNode) = MAX(thickC, cLimit)
            tLNode(iNode) = MAX(thickM, 0.0D0)
            chemical_delta_rho_list(iNode) = chemical_delta_rho
```

### `dQdTdA`

`src/MOD_Data.f90:1864`
```text
     &                    mxDOF, mxEl, mxFEl, mxNode, &             ! input
     &                    brief, &                                  ! output
     &                    continuum_LRi, &                          ! output
     &                    dQdTdA, elev, &                           ! output
     &                    fault_LRi, fDip, &                        ! output
     &                    nFakeN, nFl, nodeF, nodes, nRealN, &      ! output
     &                    numEl, numNod, n1000, offMax, offset, &   ! output
```

`src/MOD_Data.f90:1885`
```text
       INTEGER, INTENT(IN) :: iUnit7, iUnitT, mxDOF, mxEl, mxFEl, mxNode                       ! input
       LOGICAL, INTENT(OUT) :: brief                                                           ! output
       INTEGER, INTENT(OUT) :: continuum_LRi                                                   ! output
       REAL*8,  INTENT(OUT) :: dQdTdA, elev                                                    ! output
       INTEGER, INTENT(OUT) :: fault_LRi                                                       ! output
       REAL*8,  INTENT(OUT) :: fDip                                                            ! output
       INTEGER, INTENT(OUT) :: nFakeN, nFl, nodeF, nodes, nRealN, numEl, numNod, n1000         ! output
```

`src/MOD_Data.f90:1901`
```text
            & off, pLat, pLon, qi, vector, xi, yi
       DIMENSION checkE(mxEl), checkF(mxFEl), checkN(mxNode), &
     &           continuum_LRi(mxEl), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
     &           fDip(2, mxFEl), nodeF(4, mxFEl), &
     &           nodes(3, mxEl), offset(mxFEl), &
```

`src/MOD_Data.f90:2000`
```text
            xNode(i) = xi
            yNode(i) = yi
            elev(i) = elevi
            dQdTdA(i) = qi
            IF (qi < 0.0D0) THEN
			  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
			  call FatalError(ErrorMsg,ThID)
```

`src/MOD_Data.f90:2208`
```text
       SUBROUTINE PutNet (iUnitO, &                               ! INTENT(IN)
     &                    brief, &                                ! INTENT(IN)
     &                    continuum_LRi, &                        ! INTENT(IN)
     &                    dQdTdA, elev, &                         ! INTENT(IN)
     &                    fault_LRi, fDip, &                      ! INTENT(IN)
     &                    mxEl, mxFEl, mxNode, n1000, &           ! INTENT(IN)
     &                    nFakeN, nFl, nodeF, nodes, &            ! INTENT(IN)
```

`src/MOD_Data.f90:2224`
```text
       INTEGER,      INTENT(IN) :: iUnitO
       LOGICAL,      INTENT(IN) :: brief
       INTEGER,      INTENT(IN) :: continuum_LRi
       REAL*8,       INTENT(IN) :: dQdTdA, elev
       INTEGER,      INTENT(IN) :: fault_LRi
       REAL*8,       INTENT(IN) :: fDip
       INTEGER,      INTENT(IN) :: mxEl, mxFEl, mxNode, n1000, &
```

`src/MOD_Data.f90:2238`
```text
       DIMENSION chemical_delta_rho_list(mxNode), &
     &           continuum_LRi(mxEl), &
     &           cooling_curvature_list(mxNode), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
     &           fDip(2, mxFEl), &
     &           nodeF(4, mxFEl), nodes(3, mxEl), &
```

`src/MOD_Data.f90:2267`
```text
            END IF
            pLat = 90.0D0 - xNode(i) * 57.2957795130823D0
            pLon = yNode(i) * 57.2957795130823D0
            WRITE (iUnitO, 91) i, pLon, pLat, elev(i), dQdTdA(i), zMNode(i), &
     &                         tLNode(i), chemical_delta_rho_list(i), &
     &                         cooling_curvature_list(i)
   91       FORMAT (I8, 2F11.5, 6ES10.2)
```

`src/MOD_Score.f90:1079`
```text
     &                    mxDOF, mxEl, mxFEl, mxNode, &
     &                    brief, continuum_LRi, cooling_curvature, & ! output
     &                    density_anomaly, &
     &                    dQdTdA, elev, fault_LRi, fDip, &
     &                    nFakeN, nFl, nodeF, nodes, nRealN, &
     &                    numEl, numNod, n1000, offMax, offset, &
     &                    title1, tLNode, xNode, yNode, zMNode, &
```

`src/MOD_Score.f90:1093`
```text
       INTEGER, INTENT(IN) :: iUnit7, iUnitT, mxDOF, mxEl, mxFEl, mxNode                       ! input
       LOGICAL, INTENT(OUT) :: brief                                                           ! output
       INTEGER, INTENT(OUT) :: continuum_LRi                                                   ! output
       REAL*8, INTENT(OUT) :: cooling_curvature, density_anomaly, dQdTdA, elev                 ! output
       INTEGER, INTENT(OUT) :: fault_LRi                                                       ! output
       REAL*8, INTENT(OUT) :: fDip                                                             ! output
       INTEGER, INTENT(OUT) :: nFakeN, nFl, nodeF, nodes, nRealN, numEl, numNod, n1000         ! output
```

`src/MOD_Score.f90:1111`
```text
     &           continuum_LRi(mxEl), &
     &           cooling_curvature(mxNode), &
     &           density_anomaly(mxNode), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
     &           fDip(2, mxFEl), nodeF(4, mxFEl), &
     &           nodes(3, mxEl), offset(mxFEl), tLNode(mxNode), &
```

`src/MOD_Score.f90:1208`
```text
            xNode(i) = xi
            yNode(i) = yi
            elev(i) = elevi
            dQdTdA(i) = qi
            IF (qi < 0.0D0) THEN
			  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
			  call FatalError(ErrorMsg,ThID)
```

`src/MOD_Score.f90:1915`
```text


       SUBROUTINE OLDMohr (aCreep, alphaT, bCreep, Biot, Byerly, & ! input
     &                  cCreep, cFric, conduc, constr, dCreep, dQdTdA, &
     &                  eCreep, elev, fDip, fFric, fMuMax, &
     &                  fPFlt, fArg, gMean, &
     &                  mxFEl, mxNode, nFl, nodeF, &
```

`src/MOD_Score.f90:1974`
```text
       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric, conduc, &   ! input
          & constr, dCreep, dQdTdA, eCreep, elev, fDip, fFric, fMuMax, &                      ! input
          & fPFlt, fArg, gMean                                                                ! input
       INTEGER, INTENT(IN) :: mxFEl, mxNode, nFl, nodeF                                       ! input
       REAL*8, INTENT(IN) :: offMax, offset, oneKm, radio, rhoH2O, rhoBar, slide              ! input
```

`src/MOD_Score.f90:2015`
```text
       DIMENSION dLEPdZ(2), dSFdZ(2), rho(2), sheart(2), tMean(2), zTrans(2)
!      DIMENSIONs of external argument arrays:
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), dQdTdA(mxNode), elev(mxNode), &
     &           fC(2, 2, 7, mxFEl), fDip(2, mxFEl), &
     &           fIMuDZ(7, mxFEl), fPeakS(2, mxFEl), &
     &           fPFlt(2, 2, 2, 7, mxFEl), fSlips(mxFEl), &
```

`src/MOD_Score.f90:2088`
```text
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
```

`src/MOD_Score.f90:2089`
```text
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
```

`src/MOD_Score.f90:2112`
```text
                 elevat = elev(n1) * fPhi(1, m) + elev(n2) * fPhi(2, m)

!                heat flow:
                 q = dQdTdA(n1) * fPhi(1, m) + dQdTdA(n2) * fPhi(2, m)

!                crustal thickness:
                 crust = zMNode(n1) * fPhi(1, m) + zMNode(n2) * fPhi(2, m)
```

`src/MOD_Score.f90:2456`
```text

       SUBROUTINE Mohr (alphaT, conduc, constr, &                 ! input
     &                  continuum_LRi, &
     &                  dQdTdA, elev, &
     &                  fault_LRi, fDip, fMuMax, &
     &                  fPFlt, fArg, gMean, &
     &                  LRn, LR_set_fFric, LR_set_cFric, LR_set_Biot, LR_set_Byerly, &
```

`src/MOD_Score.f90:2518`
```text
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: alphaT, conduc, constr                                           ! input
       INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
       REAL*8, INTENT(IN) :: dQdTdA, elev                                                     ! input
       INTEGER, INTENT(IN) :: fault_LRi                                                       ! input
       REAL*8, INTENT(IN) :: fDip, fMuMax, fPFlt, fArg, gMean                                 ! input
       INTEGER, INTENT(IN) :: LRn                                                             ! input
```

`src/MOD_Score.f90:2562`
```text
!      DIMENSIONs of external argument arrays:
       DIMENSION alphaT(2), conduc(2), &
     &           continuum_LRi(mxEl), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
     &           fC(2, 2, 7, mxFEl), fDip(2, mxFEl), &
     &           fIMuDZ(7, mxFEl), fPeakS(2, mxFEl), &
```

`src/MOD_Score.f90:2655`
```text
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
```

`src/MOD_Score.f90:2656`
```text
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
```

`src/MOD_Score.f90:2679`
```text
                 elevat = elev(n1) * fPhi(1, m) + elev(n2) * fPhi(2, m)

!                heat flow:
                 q = dQdTdA(n1) * fPhi(1, m) + dQdTdA(n2) * fPhi(2, m)

!                crustal thickness:
                 crust = zMNode(n1) * fPhi(1, m) + zMNode(n2) * fPhi(2, m)
```

`src/MOD_Score.f90:3291`
```text


       SUBROUTINE PutNet (iUnitO, &                           ! INTENT(IN)
     &                    brief, dQdTdA, elev, fDip, &
     &                    mxEl, mxFEl, mxNode, n1000, &
     &                    nFakeN, nFl, nodeF, nodes, &
     &                    nRealN, numEl, numNod, offset, &
```

`src/MOD_Score.f90:3303`
```text
       IMPLICIT NONE
       INTEGER,                      INTENT(IN) :: iUnitO
       LOGICAL,                      INTENT(IN) :: brief
       REAL*8,  DIMENSION(mxNode),   INTENT(IN) :: dQdTdA, elev
       REAL*8,  DIMENSION(2, mxFEl), INTENT(IN) :: fDip
       INTEGER,                      INTENT(IN) :: mxEl, mxFEl, mxNode, n1000, nFakeN, nFl
       INTEGER, DIMENSION(4, mxFEl), INTENT(IN) :: nodeF
```

`src/MOD_Score.f90:3330`
```text
            END IF
            pLat = 90.0D0 - xNode(i) * degrees_per_radian
            pLon = yNode(i) * degrees_per_radian
            WRITE (iUnitO, 91) i, pLon, pLat, elev(i), dQdTdA(i), zMNode(i), tLNode(i)
   91       FORMAT (I8, 2F11.5, 4ES10.2)
  100  CONTINUE

```

`src/MOD_Shells.f90:533`
```text
END FUNCTION ATan2F

SUBROUTINE Balanc (alphaT, area, conduc, constr, &         ! input
&                    density_anomaly, detJ, dQdTdA, dXS, &
&                    dXSP, dYS, dYSP, edgeTS, elev, eta, &
&                    fArg, fC, fDip, &
&                    fIMuDZ, fLen, fPFlt, fPSfer, fTStar, &
```

`src/MOD_Shells.f90:590`
```text
IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area, conduc, constr, density_anomaly, detJ, &      ! input
				   & dQdTdA, dXS, dXSP, dYS, dYSP                                ! input
LOGICAL, INTENT(IN) :: edgeTS                                                     ! input
REAL*8, INTENT(IN) :: elev, eta, &                                                ! input
				   & fArg, fC, fDip, fIMuDZ, fLen, fPFlt, fPSfer, fTStar, gMean  ! input
```

`src/MOD_Shells.f90:634`
```text
DIMENSION fPhi(4, 7), fPoint(7), fGauss(7)
DIMENSION area(mxEl), alphaT(2), &
&           comp(6, mxDOF), conduc(2), density_anomaly(mxNode), &
&           detJ(7, mxEl), dQdTdA(mxNode), &
&           dXS(2, 2, 3, 7, mxEl), dXSP(3, 7, mxEl), &
&           dYS(2, 2, 3, 7, mxEl), dYSP(3, 7, mxEl), &
&           edgeTS(3, mxEl), elev(mxNode), eta(7, mxEl), &
```

`src/MOD_Shells.f90:765`
```text
CALL Fixed (alphaT, area, conduc, &  ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
&             dXSP, dYSP, edgeTS, elev, fDip, fLen, fPFlt, &
&             fPSfer, fArg, gMean, &
&             iCond, iUnitT, &
```

`src/MOD_Shells.f90:889`
```text
CALL Fixed (alphaT, area, conduc, &   ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
&             dXSP, dYSP, edgeTS, elev, fDip, fLen, fPFlt, &
&             fPSfer, fArg, gMean, &
&             iCond, iUnitT, &
```

`src/MOD_Shells.f90:3729`
```text
&                    continuum_LRi, &
&                    cooling_curvature, &
&                    density_anomaly, &
&                    dQdTdA, elev, &
&                    fPSfer, gMean, gradie, &
&                    iConve, iPAfri, iPVRef, iUnitM, iUnitT, &
&                    LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, &
```

`src/MOD_Shells.f90:3754`
```text
REAL*8, INTENT(IN) :: conduc                                                           ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
REAL*8, INTENT(IN) :: cooling_curvature, &                                             ! input
				   & density_anomaly, dQdTdA, elev, &                                 ! input
				   & fPSfer, gMean, gradie                                            ! input
INTEGER, INTENT(IN) :: iConve, iPAfri, iPVRef, iUnitM, iUnitT, mxEl, mxNode            ! input
INTEGER, INTENT(IN) :: LRn                                                             ! input
```

`src/MOD_Shells.f90:3790`
```text
&           curviness(7, mxEl), &
&           delta_rho(7, mxEl), &
&           density_anomaly(mxNode), &
&           dQdTdA(mxNode), &
&           elev(mxNode), &
&           fPSfer(2, 2, 3, 7, mxEl), &
&           geothC(4, 7, mxEl), geothM(4, 7, mxEl), &
```

`src/MOD_Shells.f90:3861`
```text

CALL Interp (elev, mxEl, mxNode, nodes, numEl, & ! input
&              zMoho)                              ! output
CALL Interp (dQdTdA, mxEl, mxNode, nodes, numEl, & ! input
&              tLInt)                                ! output
DO 2 m = 1, 7
	DO 1 i = 1, numEl
```

`src/MOD_Shells.f90:3916`
```text
!            N.B. On first pass, omit curviness:

		 geothC(1, m, i) = geoth1
		 q = dQdTdA(nodes(1, i)) * points(1, m) + &
&               dQdTdA(nodes(2, i)) * points(2, m) + &
&               dQdTdA(nodes(3, i)) * points(3, m)
		 geothC(2, m, i) = q / conduc(1)
```

`src/MOD_Shells.f90:3917`
```text

		 geothC(1, m, i) = geoth1
		 q = dQdTdA(nodes(1, i)) * points(1, m) + &
&               dQdTdA(nodes(2, i)) * points(2, m) + &
&               dQdTdA(nodes(3, i)) * points(3, m)
		 geothC(2, m, i) = q / conduc(1)
		 geothC(3, m, i) = geoth3
```

`src/MOD_Shells.f90:3918`
```text
		 geothC(1, m, i) = geoth1
		 q = dQdTdA(nodes(1, i)) * points(1, m) + &
&               dQdTdA(nodes(2, i)) * points(2, m) + &
&               dQdTdA(nodes(3, i)) * points(3, m)
		 geothC(2, m, i) = q / conduc(1)
		 geothC(3, m, i) = geoth3
		 geothC(4, m, i) = geoth4
```

`src/MOD_Shells.f90:3969`
```text
!   (relative to a standard pressure curve, in -SQUEEZ-):

DO 100 i = 1, numNod
	geoth2 = dQdTdA(i) / conduc(1)
	geoth3 = -0.50D0 * radio(1) / conduc(1) - 0.50D0 * cooling_curvature(i)
	geoth5 = geoth1 + &
&               geoth2 * zMNode(i) + &
```

`src/MOD_Shells.f90:4183`
```text
SUBROUTINE Fixed (alphaT, area, conduc, & ! input
&                   density_anomaly, detJ, &
&                   doFB1, doFB2, doFB3, doFB4, &
&                   dQdTdA, dXS, dYS, &
&                   dXSP, dYSP, edgeTS, elev, fDip, fLen, &
&                   fPFlt, fPSfer, fArg, gMean, &
&                   iCond, iUnitT, &
```

`src/MOD_Shells.f90:4205`
```text
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area, conduc, density_anomaly, detJ                      ! input
LOGICAL, INTENT(IN) :: doFB1, doFB2, doFB3, doFB4                                      ! input
REAL*8, INTENT(IN) :: dQdTdA, dXS, dYS, dXSP, dYSP                                     ! input
LOGICAL, INTENT(IN) :: edgeTS                                                          ! input
REAL*8, INTENT(IN) :: elev, fDip, fLen, fPFlt, fPSfer, fArg, gMean                     ! input
INTEGER, INTENT(IN) :: iCond, iUnitT, mxBn, mxDOF, mxEl, mxFEl, mxNode, &              ! input
```

`src/MOD_Shells.f90:4239`
```text
&           radio(2),  rhoBar(2), temLim(2)
DIMENSION phi(2), points(3, 7), theta(2), weight(7)
DIMENSION area(mxEl), density_anomaly(mxNode), &
&           detJ(7, mxEl), dQdTdA(mxNode), &
&           dXS(2, 2, 3, 7, mxEl), dYS(2, 2, 3, 7, mxEl), &
&           dXSP(3, 7, mxEl), dYSP(3, 7, mxEl), edgeTS(3, mxEl), &
&           elev(mxNode), fAngle(2), fBase(mxDOF), fDip(2, mxFEl), &
```

`src/MOD_Shells.f90:4489`
```text
&                                                       density_anomaly(nodes(2, kEle)), &
&                                                       density_anomaly(nodes(3, kEle)))
								  q = PhiVal(s1, s2, s3, &
&                                               dQdTdA(nodes(1, kEle)), &
&                                               dQdTdA(nodes(2, kEle)), &
&                                               dQdTdA(nodes(3, kEle)))
								  zM = PhiVal(s1, s2, s3, &
```

`src/MOD_Shells.f90:4490`
```text
&                                                       density_anomaly(nodes(3, kEle)))
								  q = PhiVal(s1, s2, s3, &
&                                               dQdTdA(nodes(1, kEle)), &
&                                               dQdTdA(nodes(2, kEle)), &
&                                               dQdTdA(nodes(3, kEle)))
								  zM = PhiVal(s1, s2, s3, &
&                                                zMNode(nodes(1, kEle)), &
```

`src/MOD_Shells.f90:4491`
```text
								  q = PhiVal(s1, s2, s3, &
&                                               dQdTdA(nodes(1, kEle)), &
&                                               dQdTdA(nodes(2, kEle)), &
&                                               dQdTdA(nodes(3, kEle)))
								  zM = PhiVal(s1, s2, s3, &
&                                                zMNode(nodes(1, kEle)), &
&                                                zMNode(nodes(2, kEle)), &
```

`src/MOD_Shells.f90:4679`
```text
&                    mxDOF, mxEl, mxFEl, mxNode, &
&                    brief, continuum_LRi, cooling_curvature, & ! output
&                    density_anomaly, &
&                    dQdTdA, elev, fault_LRi, fDip, &
&                    nFakeN, nFl, nodeF, nodes, nRealN, &
&                    numEl, numNod, n1000, offMax, offset, &
&                    title1, tLNode, xNode, yNode, zMNode, &
```

`src/MOD_Shells.f90:4693`
```text
INTEGER, INTENT(IN) :: iUnit7, iUnitT, mxDOF, mxEl, mxFEl, mxNode                       ! input
LOGICAL, INTENT(OUT) :: brief                                                           ! output
INTEGER, INTENT(OUT) :: continuum_LRi                                                   ! output
REAL*8, INTENT(OUT) :: cooling_curvature, density_anomaly, dQdTdA, elev                 ! output
INTEGER, INTENT(OUT) :: fault_LRi                                                       ! output
REAL*8, INTENT(OUT) :: fDip                                                             ! output
INTEGER, INTENT(OUT) :: nFakeN, nFl, nodeF, nodes, nRealN, numEl, numNod, n1000         ! output
```

`src/MOD_Shells.f90:4711`
```text
&           continuum_LRi(mxEl), &
&           cooling_curvature(mxNode), &
&           density_anomaly(mxNode), &
&           dQdTdA(mxNode), elev(mxNode), &
&           fault_LRi(mxFEl), &
&           fDip(2, mxFEl), nodeF(4, mxFEl), &
&           nodes(3, mxEl), offset(mxFEl), tLNode(mxNode), &
```

`src/MOD_Shells.f90:4808`
```text
	xNode(i) = xi
	yNode(i) = yi
	elev(i) = elevi
	dQdTdA(i) = qi
	IF (qi < 0.0D0) THEN
	  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
	  call FatalError(ErrorMsg,ThID)
```

`src/MOD_Shells.f90:5539`
```text

SUBROUTINE Mohr (alphaT, conduc, constr, &                 ! input
&                  continuum_LRi, &
&                  dQdTdA, elev, &
&                  fault_LRi, fDip, fMuMax, &
&                  fPFlt, fArg, gMean, &
&                  LRn, LR_set_fFric, LR_set_cFric, LR_set_Biot, LR_set_Byerly, &
```

`src/MOD_Shells.f90:5601`
```text
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, conduc, constr                                           ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
REAL*8, INTENT(IN) :: dQdTdA, elev                                                     ! input
INTEGER, INTENT(IN) :: fault_LRi                                                       ! input
REAL*8, INTENT(IN) :: fDip, fMuMax, fPFlt, fArg, gMean                                 ! input
INTEGER, INTENT(IN) :: LRn                                                             ! input
```

`src/MOD_Shells.f90:5645`
```text
!      DIMENSIONs of external argument arrays:
DIMENSION alphaT(2), conduc(2), &
&           continuum_LRi(mxEl), &
&           dQdTdA(mxNode), elev(mxNode), &
&           fault_LRi(mxFEl), &
&           fC(2, 2, 7, mxFEl), fDip(2, mxFEl), &
&           fIMuDZ(7, mxFEl), fPeakS(2, mxFEl), &
```

`src/MOD_Shells.f90:5738`
```text
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
		 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
&                          dQdTdA(n3) + dQdTdA(n4))
		 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
&                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
```

`src/MOD_Shells.f90:5739`
```text
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
		 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
&                          dQdTdA(n3) + dQdTdA(n4))
		 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
&                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
		 tMeanC = (tSurf + tTrans) / 2.0D0
```

`src/MOD_Shells.f90:5762`
```text
		 elevat = elev(n1) * fPhi(1, m) + elev(n2) * fPhi(2, m)

!                heat flow:
		 q = dQdTdA(n1) * fPhi(1, m) + dQdTdA(n2) * fPhi(2, m)

!                crustal thickness:
		 crust = zMNode(n1) * fPhi(1, m) + zMNode(n2) * fPhi(2, m)
```

`src/MOD_Shells.f90:6475`
```text
SUBROUTINE Pure (alphaT, area, &                       ! input
&                  basal, &
&                  conduc, constr, continuum_LRi, &
&                  delta_rho, detJ, dQdTdA, dXS, dYS, &
&                  elev, etaMax, everyP, &
&                  fault_LRi, fBase, fDip, fLen, fMuMax, &
&                  fPFlt, fPSfer, fArg, geothC, geothM, glue, &
```

`src/MOD_Shells.f90:6507`
```text
DOUBLE PRECISION, INTENT(IN) :: basal                                                   ! input
REAL*8, INTENT(IN) :: conduc, constr                                                    ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                    ! input
REAL*8, INTENT(IN) :: delta_rho, detJ, dQdTdA, dXS, dYS, elev, etaMax                   ! input
LOGICAL, INTENT(IN) :: everyP                                                           ! input
DOUBLE PRECISION, INTENT(IN) :: fBase                                                   ! input
INTEGER, INTENT(IN) :: fault_LRi                                                        ! input
```

`src/MOD_Shells.f90:6558`
```text
&           basal(2, mxNode), &
&           continuum_LRi(mxEl), &
&           delta_rho(7, mxEl), detJ(7, mxEl), &
&           dQdTdA(mxNode), &
&           dXS(2, 2, 3, 7, mxEl), dYS(2, 2, 3, 7, mxEl), &
&           dv(2, mxNode), dVLast(2, mxNode), &
&           elev(mxNode), eRate(3, 7, mxEl), eta(7, mxEl), &
```

`src/MOD_Shells.f90:6631`
```text
30  CONTINUE
CALL Mohr (alphaT, conduc, constr, &                     ! input
&            continuum_LRi, &
&            dQdTdA, elev, &
&            fault_LRi, fDip, fMuMax, &
&            fPFlt, fArg, gMean, &
&            LRn, LR_set_fFric, LR_set_cFric, LR_set_Biot, LR_set_Byerly, &
```

`src/MOD_Shells.f90:6695`
```text
&                   alpha, scoreC, scoreD, tOfset, zTranC) ! output
	CALL Mohr (alphaT, conduc, constr, &                     ! input
&                 continuum_LRi, &
&                 dQdTdA, elev, &
&                 fault_LRi, fDip, fMuMax, &
&                 fPFlt, fArg, gMean, &
&                 LRn, LR_set_fFric, LR_set_cFric, LR_set_Biot, LR_set_Byerly, &
```

`src/OrbData5.f90:45`
```text
integer :: nCX,nCY,nSX,nSY,iNode
integer :: nDomainX,nDomainY,nLithoX,nLithoY,domainClass,domainRow,domainCol
integer :: lithoRow,lithoRow2,lithoCol,lithoCol2
real*8 :: TAsthK,dQdTdA,elev,fDip
real*8 :: offset,xNode,yNode,area,detJ,dXs,dYs,dXSP,dYSP,fLen,fpflt,fpsfer,fArg,sita
real*8 :: eX1,eX2,eDX,eY1,eY2,eDY
real*8 :: qX1,qX2,qDX,qY1,qY2,qDY,qLimit,aX1,aX2,aDX,aY1,aY2,aDY
```

`src/OrbData5.f90:104`
```text

!  DIMENSIONS using PARAMETER maxNod:
       DIMENSION checkN(maxNod), chemical_delta_rho_list(maxNod), &
     &           cooling_curvature_list(maxNod), dQdTdA(maxNod), &
     &           elev  (maxNod), &
     &           tLNode(maxNod), &
     &           xNode (maxNod), yNode (maxNod), zMNode(maxNod)
```

`src/OrbData5.f90:302`
```text
     &               mxDOF,  mxEl,  mxFEl, mxNode, &           ! INTENT(IN)
     &               brief, &                                  ! INTENT(OUT)
     &               continuum_LRi, &                          ! INTENT(OUT)
     &               dQdTdA,   elev, &                         ! INTENT(OUT)
     &               fault_LRi, fDip, &                        ! INTENT(OUT)
     &               nFakeN,    nFl,  nodeF,  nodes, nRealN, & ! INTENT(OUT)
     &               numEl, numNod,  n1000, offMax, offset, &  ! INTENT(OUT)
```

`src/OrbData5.f90:369`
```text

       needQ = .FALSE.
       DO 70 i = 1, numNod
            IF (dQdTdA(i) == 0.0D0) needQ = .TRUE.
   70  CONTINUE

       IF (needQ) THEN
```

`src/OrbData5.f90:392`
```text

       DO 80 i = 1, numNod
            qLimit = qLim0 + dQL_dE * elev(i)
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE

```

`src/OrbData5.f90:393`
```text
       DO 80 i = 1, numNod
            qLimit = qLim0 + dQL_dE * elev(i)
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE

!      Read dataset of gridded seafloor ages, on unit 7:
```

`src/OrbData5.f90:477`
```text
  600  FORMAT (/' Computing layer thicknesses at all nodes...' &
     &         /'        0 nodes completed...')
       WRITE (iUnitL, 601)
  601  FORMAT ('  NODE LONGITUDE  LATITUDE      ELEV    dQdTdA', &
     &         '    zMNode    tLNode', &
     &         ' chemical_Delta_rho cooling_curvature')
       DO 680 iNode = 1, numNod
```

`src/OrbData5.f90:484`
```text
            pLon = yNode(iNode) * 57.2957795130823D0
            pLat = 90.0D0 - xNode(iNode) * 57.2957795130823D0
            elevat = elev(iNode)
            heatFl = dQdTdA(iNode)

            arcanaOcean=.FALSE.
            requestedTotalLithosphere=0.0D0
```

`src/OrbData5.f90:546`
```text
     &                   ModNum)

            elev(iNode) = elevat
            dQdTdA(iNode) = heatFl
            zMNode(iNode) = MAX(thickC, cLimit)
            tLNode(iNode) = MAX(thickM, 0.0D0)
            chemical_delta_rho_list(iNode) = chemical_delta_rho
```

`src/OrbData5.f90:552`
```text
            chemical_delta_rho_list(iNode) = chemical_delta_rho
            cooling_curvature_list(iNode) = cooling_curvature
            WRITE (iUnitL, 678) iNode, pLon, pLat, &
     &                          elev(iNode), dQdTdA(iNode), zMNode(iNode), &
     &                          tLNode(iNode), &
     &                          chemical_delta_rho_list(iNode), &
     &                          cooling_curvature_list(iNode)
```

`src/OrbData5.f90:568`
```text
       call PutNet (   14, &                                   ! INTENT(IN)
     &              brief, &                                   ! INTENT(IN)
     &              continuum_LRi, &                           ! INTENT(IN)
     &              dQdTdA,   elev, &                          ! INTENT(IN)
     &              fault_LRi, fDip, &                         ! INTENT(IN)
     &              mxEl,  mxFEl, mxNode,  n1000, &            ! INTENT(IN)
     &              nFakeN,    nFl,  nodeF,  nodes, &          ! INTENT(IN)
```

`src/OrbScore2.f90:205`
```text

!  DIMENSIONs using PARAMETER maxNod:
       LOGICAL :: checkN
       REAL*8  :: atnode, cooling_curvature, density_anomaly, dQdTdA, eDotNC, eDotNM, elev, &
                & tLNode, uvecN, xNode, yNode, zMNode
       DIMENSION atnode (maxNod), checkN (maxNod), &
     &           cooling_curvature(maxNod), density_anomaly(maxNod), &
```

`src/OrbScore2.f90:209`
```text
                & tLNode, uvecN, xNode, yNode, zMNode
       DIMENSION atnode (maxNod), checkN (maxNod), &
     &           cooling_curvature(maxNod), density_anomaly(maxNod), &
     &           dQdTdA (maxNod), &
     &           eDotNC (maxNod), eDotNM (maxNod), &
     &           elev   (maxNod), &
     &           tLNode (maxNod), &
```

`src/OrbScore2.f90:712`
```text
     &              mxDOF, mxEl, mxFEl, mxNode, &
     &              brief, continuum_LRi, cooling_curvature, &  ! output
     &              density_anomaly, &
     &              dQdTdA, elev, fault_LRi, fDip, &
     &              nFakeN, nFl, nodeF, nodes, nRealN, &
     &              numEl, numNod, n1000, offMax, offset, &
     &              title1, tLNode, xNode, yNode, zMNode, &
```

`src/OrbScore2.f90:1058`
```text
       DO iMohr = 1, 3
           CALL Mohr (alphaT, conduc, constr, &                     ! input
         &            continuum_LRi, &
         &            dQdTdA, elev, &
         &            fault_LRi, fDip, fMuMax, &
         &            fPFlt, fArg, gMean, &
         &            LRn, LR_set_fFric, LR_set_cFric, LR_set_Biot, LR_set_Byerly, &
```

`src/SHELLS_v5.0.f90:81`
```text
!   DIMENSIONs that will be ALLOCATEd based on variable mxNode:
       INTEGER, DIMENSION(:), ALLOCATABLE :: jCol1, jCol2, whichP
       LOGICAL, DIMENSION(:), ALLOCATABLE :: checkN
       REAL*8,    DIMENSION(:), ALLOCATABLE :: atNode, dQdTdA, elev, tauZZN, &
     &                                         tLNode, xNode, yNode, zMNode
       REAL*8,    DIMENSION(:), ALLOCATABLE :: density_anomaly, &
     &                                         cooling_curvature
```

`src/SHELLS_v5.0.f90:384`
```text
     &           checkN(mxNode), &
     &           cooling_curvature(mxNode), &
     &           density_anomaly(mxNode), &
     &           dQdTdA(mxNode), &
     &           dv(2, mxNode), dVLast(2, mxNode), &
     &           elev(mxNode), jCol1(mxNode), jCol2(mxNode), &
     &           tauZZN(mxNode), tLNode(mxNode), &
```

`src/SHELLS_v5.0.f90:468`
```text
     &              mxDOF, mxEl, mxFEl, mxNode, &
     &              brief, continuum_LRi, cooling_curvature, &  ! output
     &              density_anomaly, &
     &              dQdTdA, elev, fault_LRi, fDip, &
     &              nFakeN, nFl, nodeF, nodes, nRealN, &
     &              numEl, numNod, n1000, offMax, offset, &
     &              title1, tLNode, xNode, yNode, zMNode, &
```

`src/SHELLS_v5.0.f90:679`
```text
     &              continuum_LRi, &
     &              cooling_curvature, &
     &              density_anomaly, &
     &              dQdTdA, elev, &
     &              fPSfer, gMean, gradie, &
     &              iConve, iPAfri, iPVRef, iUnitM, iUnitLog, &
     &              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, &
```

### `needQ`

`src/MOD_Data.f90:283`
```text
!---------------------------------------------------------------------
        !Internal variables:
        INTEGER :: ic1, ic2, ir1, ir2
        LOGICAL :: badP, badT, outsid, needE, needQ, &
      &            warnC1, warnC2, warnM1, warnL2, wayOut
        REAL*8  :: ageMa, bot, c0_of_mantle_gradient, c1_of_mantle_gradient, &
                 & deltaQ, delta_quadratic, delta_T, delta_tS, fc, fr, &
```

`src/MOD_Data.f90:381`
```text

!   Determine heat-flow, in needed:

       needQ = (heatFl == 0.0D0)
       IF (needQ) THEN
            ir1 = ((qY2 - pLat) / qDY) + 1.00001D0 ! truncated to INTEGER
            ir1 = MAX(ir1, 1)
```

`src/MOD_Data.f90:382`
```text
!   Determine heat-flow, in needed:

       needQ = (heatFl == 0.0D0)
       IF (needQ) THEN
            ir1 = ((qY2 - pLat) / qDY) + 1.00001D0 ! truncated to INTEGER
            ir1 = MAX(ir1, 1)
            ir1 = MIN(ir1, nQY - 1)
```

`src/OrbData5.f90:85`
```text

       INTEGER :: continuum_LRi, fault_LRi ! both DIMENSIONed below ...

       LOGICAL :: brief, log_strike_adjustments, needE, needQ, skipBC
       LOGICAL :: arcanaMode,arcana15Open,arcana16Open,arcanaOcean
       LOGICAL :: checkE, checkF, checkN, edgeTS, edgeFS

```

`src/OrbData5.f90:367`
```text

!   Read in heat-flow array on unit 4, if needed:

       needQ = .FALSE.
       DO 70 i = 1, numNod
            IF (dQdTdA(i) == 0.0D0) needQ = .TRUE.
   70  CONTINUE
```

`src/OrbData5.f90:369`
```text

       needQ = .FALSE.
       DO 70 i = 1, numNod
            IF (dQdTdA(i) == 0.0D0) needQ = .TRUE.
   70  CONTINUE

       IF (needQ) THEN
```

`src/OrbData5.f90:372`
```text
            IF (dQdTdA(i) == 0.0D0) needQ = .TRUE.
   70  CONTINUE

       IF (needQ) THEN
            IF(Verbose) WRITE(iUnitVerb, 71)
   71       FORMAT(/ /' Attempting to read gridded heat-flow:'/)
            READ (4, * ) qX1, qDX, qX2
```

### `qArray`

`src/MOD_Data.f90:219`
```text
     &                     oneKm, &                                                         ! INTENT(IN)
     &                      pLon,   pLat, &                                                 ! INTENT(IN)
     &                     qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                    TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
```

`src/MOD_Data.f90:265`
```text
                           &  oneKm, &
                           &   pLon,   pLat, &
                           &  qLim0, dQL_dE,  qLim1, &
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
                           & TAsthK, temLim,  TSurf
```

`src/MOD_Data.f90:277`
```text
        LOGICAL, INTENT(IN) :: arcanaMode,arcanaOcean
        REAL*8, INTENT(IN) :: requestedTotalLithosphere
        !Argument arrays ALLOCATED and dimensioned in calling program:
        DIMENSION aArray(:, :), cArray(:, :), eArray(:, :), qArray(:, :), sArray(:, :)
        !Argument arrays with (crust:mantle) values:
        DIMENSION alphaT(2), conduc(2), radio(2), rhoBar(2), temLim(2)
!---------------------------------------------------------------------
```

`src/MOD_Data.f90:414`
```text
     &                         (fc < -1.01D0).OR.(fc > 2.01D0)
            fr = MIN(1.0D0, MAX(0.0D0, fr))
            fc = MIN(1.0D0, MAX(0.0D0, fc))
            top = qArray(ir1, ic1) + fc * (qArray(ir1, ic2) - qArray(ir1, ic1))
            bot = qArray(ir2, ic1) + fc * (qArray(ir2, ic2) - qArray(ir2, ic1))
            heatFl = top + fr * (bot - top)

```

`src/MOD_Data.f90:415`
```text
            fr = MIN(1.0D0, MAX(0.0D0, fr))
            fc = MIN(1.0D0, MAX(0.0D0, fc))
            top = qArray(ir1, ic1) + fc * (qArray(ir1, ic2) - qArray(ir1, ic1))
            bot = qArray(ir2, ic1) + fc * (qArray(ir2, ic2) - qArray(ir2, ic1))
            heatFl = top + fr * (bot - top)

!           Check for seafloor-age overriding heat-flow grid value:
```

`src/OrbData5.f90:98`
```text
!                        DIMENSION statements:

!  DIMENSIONs using dynamic memory allocation:
       REAL*8, DIMENSION(:, :), ALLOCATABLE :: eArray, qArray, aArray, &
     &                                         cArray, sArray, arcanaDomainArray, &
     &                                         arcanaLithosphereArray

```

`src/OrbData5.f90:379`
```text
            READ (4, * ) qY1, qDY, qY2
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
            ALLOCATE ( qArray(nQY, nQX) )
            READ (4, * ) ((qArray(iRow, jCol), jCol = 1, nQX), iRow = 1, nQY)
       ELSE ! all heat-flow values at nodes are already present in .FEG file.
            IF(Verbose) WRITE(iUnitVerb, 79)
```

`src/OrbData5.f90:380`
```text
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
            ALLOCATE ( qArray(nQY, nQX) )
            READ (4, * ) ((qArray(iRow, jCol), jCol = 1, nQX), iRow = 1, nQY)
       ELSE ! all heat-flow values at nodes are already present in .FEG file.
            IF(Verbose) WRITE(iUnitVerb, 79)
   79       FORMAT (/' All nodes have non-zero heat-flow.' &
```

`src/OrbData5.f90:536`
```text
     &                    oneKm, &                                                         ! INTENT(IN)
     &                     pLon,   pLat, &                                                 ! INTENT(IN)
     &                    qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                   TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
```

### `qLim0`

`src/MOD_Data.f90:218`
```text
     &                    iUnitL, iUnitT, &                                                 ! INTENT(IN)
     &                     oneKm, &                                                         ! INTENT(IN)
     &                      pLon,   pLat, &                                                 ! INTENT(IN)
     &                     qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

`src/MOD_Data.f90:264`
```text
                           &  gMean,  hCMax,  hLMax, &
                           &  oneKm, &
                           &   pLon,   pLat, &
                           &  qLim0, dQL_dE,  qLim1, &
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
```

`src/MOD_Data.f90:443`
```text

!  Apply limits on Q:

       qLimit = qLim0 + dQL_dE * elevat
       heatFl = MAX(heatFl, qLimit)
       heatFl = MIN(heatFl, qLim1)

```

`src/MOD_Data.f90:630`
```text
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
```

`src/OrbData5.f90:153`
```text
       COMMON / fGList / fGauss
!-------------------------------------------------------------------
!                       DATA statements
!   "qLim0" is the lower limit on heat-flow for points
!      with an elevation of zero.
       REAL*8,PARAMETER :: qLim0 = 0.000D0 ! units of (watts per square meter)

```

`src/OrbData5.f90:155`
```text
!                       DATA statements
!   "qLim0" is the lower limit on heat-flow for points
!      with an elevation of zero.
       REAL*8,PARAMETER :: qLim0 = 0.000D0 ! units of (watts per square meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)
```

`src/OrbData5.f90:158`
```text
       REAL*8,PARAMETER :: qLim0 = 0.000D0 ! units of (watts per square meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)

!   "dQL_dE" is the derivitive d(qLim0)/d(elevation),
!    which adjusts the minimum heat-flow for elevation.
```

`src/OrbData5.f90:160`
```text
!  [N.B. Former limit, in program OrbData, was:}
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)

!   "dQL_dE" is the derivitive d(qLim0)/d(elevation),
!    which adjusts the minimum heat-flow for elevation.
       REAL*8,PARAMETER :: dQL_dE = 0.00D-06 ! units of (watts per square meter)/(meter)

```

`src/OrbData5.f90:246`
```text
     & /'    is chosen to lie on the asthenosphere adiabat' &
     & /'   (evaluated at an arbitrary depth of 100 km).')

       IF(Verbose) WRITE (iUnitVerb, 3) qLim0, dQL_dE, qLim1
    3  FORMAT ( &
     & /' If any elevation is non-zero, this elevation will be left' &
     & /'    unchanged, to preserve effects of hand-editing.' &
```

`src/OrbData5.f90:273`
```text

!    Echo the limits that are compiled-in-place, for a complete record:

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
```

`src/OrbData5.f90:275`
```text

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
    5  FORMAT(/' The following limits apply in this run:' &
     &/'    Lower limit on heat-flow = ', F5.3, '+', ES10.3, ' * elevation' &
```

`src/OrbData5.f90:391`
```text
!    thick and stiff lithosphere anywhere:

       DO 80 i = 1, numNod
            qLimit = qLim0 + dQL_dE * elev(i)
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE
```

`src/OrbData5.f90:535`
```text
     &                   iUnitL, iUnitVerb, &                                                 ! INTENT(IN)
     &                    oneKm, &                                                         ! INTENT(IN)
     &                     pLon,   pLat, &                                                 ! INTENT(IN)
     &                    qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

### `dQL_dE`

`src/MOD_Data.f90:218`
```text
     &                    iUnitL, iUnitT, &                                                 ! INTENT(IN)
     &                     oneKm, &                                                         ! INTENT(IN)
     &                      pLon,   pLat, &                                                 ! INTENT(IN)
     &                     qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

`src/MOD_Data.f90:264`
```text
                           &  gMean,  hCMax,  hLMax, &
                           &  oneKm, &
                           &   pLon,   pLat, &
                           &  qLim0, dQL_dE,  qLim1, &
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
```

`src/MOD_Data.f90:443`
```text

!  Apply limits on Q:

       qLimit = qLim0 + dQL_dE * elevat
       heatFl = MAX(heatFl, qLimit)
       heatFl = MIN(heatFl, qLim1)

```

`src/MOD_Data.f90:630`
```text
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
```

`src/OrbData5.f90:160`
```text
!  [N.B. Former limit, in program OrbData, was:}
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)

!   "dQL_dE" is the derivitive d(qLim0)/d(elevation),
!    which adjusts the minimum heat-flow for elevation.
       REAL*8,PARAMETER :: dQL_dE = 0.00D-06 ! units of (watts per square meter)/(meter)

```

`src/OrbData5.f90:162`
```text

!   "dQL_dE" is the derivitive d(qLim0)/d(elevation),
!    which adjusts the minimum heat-flow for elevation.
       REAL*8,PARAMETER :: dQL_dE = 0.00D-06 ! units of (watts per square meter)/(meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)
```

`src/OrbData5.f90:165`
```text
       REAL*8,PARAMETER :: dQL_dE = 0.00D-06 ! units of (watts per square meter)/(meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)

!   "qLim1 is the upper limit on heat-flow for all points.
       REAL*8,PARAMETER :: qLim1 = 0.300D0 ! units of (watts per square meter)
```

`src/OrbData5.f90:246`
```text
     & /'    is chosen to lie on the asthenosphere adiabat' &
     & /'   (evaluated at an arbitrary depth of 100 km).')

       IF(Verbose) WRITE (iUnitVerb, 3) qLim0, dQL_dE, qLim1
    3  FORMAT ( &
     & /' If any elevation is non-zero, this elevation will be left' &
     & /'    unchanged, to preserve effects of hand-editing.' &
```

`src/OrbData5.f90:273`
```text

!    Echo the limits that are compiled-in-place, for a complete record:

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
```

`src/OrbData5.f90:275`
```text

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
    5  FORMAT(/' The following limits apply in this run:' &
     &/'    Lower limit on heat-flow = ', F5.3, '+', ES10.3, ' * elevation' &
```

`src/OrbData5.f90:391`
```text
!    thick and stiff lithosphere anywhere:

       DO 80 i = 1, numNod
            qLimit = qLim0 + dQL_dE * elev(i)
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE
```

`src/OrbData5.f90:535`
```text
     &                   iUnitL, iUnitVerb, &                                                 ! INTENT(IN)
     &                    oneKm, &                                                         ! INTENT(IN)
     &                     pLon,   pLat, &                                                 ! INTENT(IN)
     &                    qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

### `qLim1`

`src/MOD_Data.f90:218`
```text
     &                    iUnitL, iUnitT, &                                                 ! INTENT(IN)
     &                     oneKm, &                                                         ! INTENT(IN)
     &                      pLon,   pLat, &                                                 ! INTENT(IN)
     &                     qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

`src/MOD_Data.f90:264`
```text
                           &  gMean,  hCMax,  hLMax, &
                           &  oneKm, &
                           &   pLon,   pLat, &
                           &  qLim0, dQL_dE,  qLim1, &
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
```

`src/MOD_Data.f90:424`
```text
     &          ((.NOT. arcanaMode) .AND. ageMa < 200.0D0)) THEN
!              Seafloor age is valid (not "unknown" or "continental")
                 IF (ageMa <= 0.0D0) THEN
                      heatFl = qLim1
                 ELSE
!                     Carol A. Stein & Seth Stein [1992]
!                     A model for the global variation in oceanic
```

`src/MOD_Data.f90:445`
```text

       qLimit = qLim0 + dQL_dE * elevat
       heatFl = MAX(heatFl, qLimit)
       heatFl = MIN(heatFl, qLim1)

!  Obtain crustal thickness from grid cArray:

```

`src/MOD_Data.f90:520`
```text
!           spreadsheet S20RTS_delta_ts_vs_age.xls for calibration).

            q_gdh1 = MAX(q_gdh1, qLimit)
            q_gdh1 = MIN(q_gdh1, qLim1)
            q_radioactivity = 0.007D0
            delta_T = TAsthK - TSurf
            h_Earth3 = (delta_T * conduc(2)) / (q_gdh1 - q_radioactivity)
```

`src/MOD_Data.f90:632`
```text
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
```

`src/OrbData5.f90:167`
```text
!  [N.B. Former limit, in program OrbData, was:}
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)

!   "qLim1 is the upper limit on heat-flow for all points.
       REAL*8,PARAMETER :: qLim1 = 0.300D0 ! units of (watts per square meter)

!   "cLimit" is a lower-limit on crustal thickness:
```

`src/OrbData5.f90:168`
```text
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)

!   "qLim1 is the upper limit on heat-flow for all points.
       REAL*8,PARAMETER :: qLim1 = 0.300D0 ! units of (watts per square meter)

!   "cLimit" is a lower-limit on crustal thickness:
       REAL*8,PARAMETER :: cLimit = 6570.0D0 ! meters
```

`src/OrbData5.f90:246`
```text
     & /'    is chosen to lie on the asthenosphere adiabat' &
     & /'   (evaluated at an arbitrary depth of 100 km).')

       IF(Verbose) WRITE (iUnitVerb, 3) qLim0, dQL_dE, qLim1
    3  FORMAT ( &
     & /' If any elevation is non-zero, this elevation will be left' &
     & /'    unchanged, to preserve effects of hand-editing.' &
```

`src/OrbData5.f90:273`
```text

!    Echo the limits that are compiled-in-place, for a complete record:

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
```

`src/OrbData5.f90:275`
```text

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
    5  FORMAT(/' The following limits apply in this run:' &
     &/'    Lower limit on heat-flow = ', F5.3, '+', ES10.3, ' * elevation' &
```

`src/OrbData5.f90:393`
```text
       DO 80 i = 1, numNod
            qLimit = qLim0 + dQL_dE * elev(i)
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE

!      Read dataset of gridded seafloor ages, on unit 7:
```

`src/OrbData5.f90:535`
```text
     &                   iUnitL, iUnitVerb, &                                                 ! INTENT(IN)
     &                    oneKm, &                                                         ! INTENT(IN)
     &                     pLon,   pLat, &                                                 ! INTENT(IN)
     &                    qLim0, dQL_dE,  qLim1, &                                         ! INTENT(IN)
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
```

### `ageMa`

`src/MOD_Data.f90:285`
```text
        INTEGER :: ic1, ic2, ir1, ir2
        LOGICAL :: badP, badT, outsid, needE, needQ, &
      &            warnC1, warnC2, warnM1, warnL2, wayOut
        REAL*8  :: ageMa, bot, c0_of_mantle_gradient, c1_of_mantle_gradient, &
                 & deltaQ, delta_quadratic, delta_T, delta_tS, fc, fr, &
                 & geoth1, geoth2, geoth3, geoth4, geoth5, geoth6, geoth7, geoth8, &
                 & h_Earth3, h_Earth5, h_plate, m_star, &
```

`src/MOD_Data.f90:377`
```text
       fc = MIN(1.0D0, MAX(0.0D0, fc))
       top = aArray(ir1, ic1) + fc * (aArray(ir1, ic2) - aArray(ir1, ic1))
       bot = aArray(ir2, ic1) + fc * (aArray(ir2, ic2) - aArray(ir2, ic1))
       ageMa = top + fr * (bot - top)

!   Determine heat-flow, in needed:

```

`src/MOD_Data.f90:421`
```text
!           Check for seafloor-age overriding heat-flow grid value:

            IF ((arcanaMode .AND. arcanaOcean) .OR. &
     &          ((.NOT. arcanaMode) .AND. ageMa < 200.0D0)) THEN
!              Seafloor age is valid (not "unknown" or "continental")
                 IF (ageMa <= 0.0D0) THEN
                      heatFl = qLim1
```

`src/MOD_Data.f90:423`
```text
            IF ((arcanaMode .AND. arcanaOcean) .OR. &
     &          ((.NOT. arcanaMode) .AND. ageMa < 200.0D0)) THEN
!              Seafloor age is valid (not "unknown" or "continental")
                 IF (ageMa <= 0.0D0) THEN
                      heatFl = qLim1
                 ELSE
!                     Carol A. Stein & Seth Stein [1992]
```

`src/MOD_Data.f90:431`
```text
!                     depth and heat flow with lithospheric age,
!                     Nature, v. 359, 10 September, p. 123-129.
!                     According to their preferred GDH1 model:
                      IF (ageMa <= 55.0D0) THEN
                           heatFl = 0.510D0 / SQRT(ageMa)
                      ELSE
                           heatFl = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
```

`src/MOD_Data.f90:432`
```text
!                     Nature, v. 359, 10 September, p. 123-129.
!                     According to their preferred GDH1 model:
                      IF (ageMa <= 55.0D0) THEN
                           heatFl = 0.510D0 / SQRT(ageMa)
                      ELSE
                           heatFl = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
                      END IF
```

`src/MOD_Data.f90:434`
```text
                      IF (ageMa <= 55.0D0) THEN
                           heatFl = 0.510D0 / SQRT(ageMa)
                      ELSE
                           heatFl = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
                      END IF
                 END IF
            END IF
```

`src/MOD_Data.f90:498`
```text
!     node has known (and valid) sea-floor age:

       IF ((arcanaMode .AND. arcanaOcean) .OR. &
     &     ((.NOT. arcanaMode) .AND. ageMa < 200.0D0)) THEN

!           This node is in oceanic lithosphere.

```

`src/MOD_Data.f90:509`
```text
!           depth and heat flow with lithospheric age,
!           Nature, v. 359, 10 September, p. 123-129.
!           According to their preferred GDH1 model:
            IF (ageMa <= 55.0D0) THEN
                 q_gdh1 = 0.510D0 / SQRT(ageMa)
            ELSE
                 q_gdh1 = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
```

`src/MOD_Data.f90:510`
```text
!           Nature, v. 359, 10 September, p. 123-129.
!           According to their preferred GDH1 model:
            IF (ageMa <= 55.0D0) THEN
                 q_gdh1 = 0.510D0 / SQRT(ageMa)
            ELSE
                 q_gdh1 = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
            END IF
```

`src/MOD_Data.f90:512`
```text
            IF (ageMa <= 55.0D0) THEN
                 q_gdh1 = 0.510D0 / SQRT(ageMa)
            ELSE
                 q_gdh1 = 0.048D0 + 0.096D0 * EXP(-0.0278D0 * ageMa)
            END IF

!        (2)Find total lithosphere thickness expected according to
```

### `alphaT`

`INPUT/iEarth5-049.in:23`
```text
9.8             gMean  = gravitational acceleration at surface of planet, m/s**2 (e.g., 9.8 for Earth)
1000.           oneKm  = length of 1 kilometer, expressed in current length units (e.g., 1000. meters if using SI units)
6371000.        radius = mean radius of the planet, in m (if using SI units) (e.g., 6371000. for Earth)
2.4E-5,3.94E-5  alphaT = volumetric thermal expansion coefficients, in /C or /K, crust/mantle
2.7,3.20        conduc = thermal conductivity, crust/mantle (for SI units, in W/m/C)
3.5E-7,3.2E-8   radio = volumetric radioactive heat production (for SI units, in W/m**3)
273.            tSurf = surface temperature of planet, in K
```

`src/MOD_Data.f90:43`
```text
       END FUNCTION ATan2F


       SUBROUTINE Squeez (alphaT, density_anomaly_kgpm3, elevat, &  ! INTENT(IN)
     &                    geoth1, geoth2, geoth3, geoth4, &         ! INTENT(IN)
     &                    geoth5, geoth6, geoth7, geoth8, &         ! INTENT(IN)
     &                     gMean, &                                 ! INTENT(IN)
```

`src/MOD_Data.f90:68`
```text
!      the given topography, instead of vice-versa.

       IMPLICIT NONE
       REAL*8, INTENT(IN) :: alphaT, density_anomaly_kgpm3, elevat, &
                           & geoth1, geoth2, geoth3, geoth4,        &
                           & geoth5, geoth6, geoth7, geoth8,        &
                           &  gMean
```

`src/MOD_Data.f90:77`
```text
                           & temLim,    zM,  zStop
       REAL*8, INTENT(OUT) :: tauZZ, sigZZB
!   Argument arrays:
       DIMENSION alphaT(2), rhoBar(2), temLim(2)

       INTEGER, PARAMETER :: nDRef = 300
       INTEGER :: i, j, lastDR, layer1, layer2, n1, n2, nStep
```

`src/MOD_Data.f90:96`
```text
!   Create reference temperature & density profiles to depth of nDRef km:

       IF (.NOT.called) THEN
            rhoTop = rhoBar(1) * (1.0D0 - alphaT(1) * geoth1)
            dRef(1) = rhoH2O
            dRef(2) = rhoH2O
            dRef(3) = 0.7D0 * rhoH2O + 0.3D0 * rhoTop
```

`src/MOD_Data.f90:120`
```text
!        Land:
            zTop = -elevat
            zBase = zStop - elevat
            dense1 = rhoBar(1) * (1.0D0 - geoth1 * alphaT(1)) + density_anomaly_kgpm3
            h = 0.0D0
            layer1 = 1
       ELSE
```

`src/MOD_Data.f90:149`
```text
            IF (h > 0.0D0) THEN
                 IF (h <= zM) THEN
                      T = tempC(h)
                      dense2 = rhoBar(1) * (1. - T * alphaT(1)) + density_anomaly_kgpm3
                      layer2 = 1
                 ELSE
                      T = tempM(h - zM)
```

`src/MOD_Data.f90:153`
```text
                      layer2 = 1
                 ELSE
                      T = tempM(h - zM)
                      dense2 = rhoBar(2) * (1. - T * alphaT(2)) + density_anomaly_kgpm3
                      layer2 = 2
                 END IF
            ELSE
```

`src/MOD_Data.f90:191`
```text
       z = zBase
       IF (zStop <= zM) THEN
            T = tempC(h)
            dense2 = rhoBar(1) * (1.0D0 - T * alphaT(1)) + density_anomaly_kgpm3
       ELSE
            T = tempM(h - zM)
            dense2 = rhoBar(2) * (1.0D0 - T * alphaT(2)) + density_anomaly_kgpm3
```

`src/MOD_Data.f90:194`
```text
            dense2 = rhoBar(1) * (1.0D0 - T * alphaT(1)) + density_anomaly_kgpm3
       ELSE
            T = tempM(h - zM)
            dense2 = rhoBar(2) * (1.0D0 - T * alphaT(2)) + density_anomaly_kgpm3
       END IF
       dense = 0.5D0 * (dense1 + dense2)
       IF (z > 0.0D0) THEN
```

`src/MOD_Data.f90:210`
```text
       END SUBROUTINE Squeez

       SUBROUTINE Assign (aArray,    aX1,    aDX,    aX2,    nAX,    aDY,    aY2,    nAY, & ! INTENT(IN)
     &                    alphaT, cLimit, conduc, &                                         ! INTENT(IN)
     &                    cArray,    cX1,    cDX,    cX2,    nCX,    cDY,    cY2,    nCY, & ! INTENT(IN)
     &                    delta_rho_limit, &                                                ! INTENT(IN)
     &                    eArray,    eX1,    eDX,    eX2,    nEX,    eDY,    eY2,    nEY, & ! INTENT(IN)
```

`src/MOD_Data.f90:257`
```text
!   syntax revision to Fortran 90 by Peter Bird, UCLA, December 2018.
       IMPLICIT NONE
       REAL*8, INTENT(IN) :: aArray,    aX1,    aDX,    aX2,    aDY,    aY2, &
                           & alphaT, cLimit, conduc, &
                           & cArray,    cX1,    cDX,    cX2,    cDY,    cY2, &
                           & delta_rho_limit, &
                           & eArray,    eX1,    eDX,    eX2,    eDY,    eY2, &
```

`src/MOD_Data.f90:279`
```text
        !Argument arrays ALLOCATED and dimensioned in calling program:
        DIMENSION aArray(:, :), cArray(:, :), eArray(:, :), qArray(:, :), sArray(:, :)
        !Argument arrays with (crust:mantle) values:
        DIMENSION alphaT(2), conduc(2), radio(2), rhoBar(2), temLim(2)
!---------------------------------------------------------------------
        !Internal variables:
        INTEGER :: ic1, ic2, ir1, ir2
```

`src/MOD_Data.f90:705`
```text
       chemical_delta_rho = 0.0D0
!     (Try this case first; adjust density_anomaly below.)

       CALL Squeez (alphaT, chemical_delta_rho, elevat, & ! INTENT(IN)
     &              geoth1, geoth2, geoth3, geoth4, &     ! INTENT(IN)
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &               gMean, iUnitT, &                     ! INTENT(IN)
```

`src/MOD_Data.f90:724`
```text

!   Repeat isostasy test:

       CALL Squeez (alphaT, chemical_delta_rho, elevat, & ! INTENT(IN)
     &              geoth1, geoth2, geoth3, geoth4, &     ! INTENT(IN)
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &              gMean, iUnitT, &                      ! INTENT(IN)
```

`src/MOD_Score.f90:1914`
```text
       END SUBROUTINE Limits


       SUBROUTINE OLDMohr (aCreep, alphaT, bCreep, Biot, Byerly, & ! input
     &                  cCreep, cFric, conduc, constr, dCreep, dQdTdA, &
     &                  eCreep, elev, fDip, fFric, fMuMax, &
     &                  fPFlt, fArg, gMean, &
```

`src/MOD_Score.f90:1973`
```text

       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric, conduc, &   ! input
          & constr, dCreep, dQdTdA, eCreep, elev, fDip, fFric, fMuMax, &                      ! input
          & fPFlt, fArg, gMean                                                                ! input
       INTEGER, INTENT(IN) :: mxFEl, mxNode, nFl, nodeF                                       ! input
```

`src/MOD_Score.f90:2014`
```text
!      DIMENSIONs of internal convenience arrays:
       DIMENSION dLEPdZ(2), dSFdZ(2), rho(2), sheart(2), tMean(2), zTrans(2)
!      DIMENSIONs of external argument arrays:
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), dQdTdA(mxNode), elev(mxNode), &
     &           fC(2, 2, 7, mxFEl), fDip(2, mxFEl), &
     &           fIMuDZ(7, mxFEl), fPeakS(2, mxFEl), &
```

`src/MOD_Score.f90:2093`
```text
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * Biot)
                 thrust = dLEPdC * cGamma
                 normal = dLEPdC / cGamma
```

`src/MOD_Score.f90:2134`
```text
                 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
                 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
                 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
```

`src/MOD_Score.f90:2135`
```text

!                mean densities:
                 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
                 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
                 dLEPdZ(1) = gMean * (rho(1) - rhoH2O * Biot)
```

`src/MOD_Score.f90:2454`
```text
       END SUBROUTINE OLDMohr


       SUBROUTINE Mohr (alphaT, conduc, constr, &                 ! input
     &                  continuum_LRi, &
     &                  dQdTdA, elev, &
     &                  fault_LRi, fDip, fMuMax, &
```

`src/MOD_Score.f90:2516`
```text

       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: alphaT, conduc, constr                                           ! input
       INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
       REAL*8, INTENT(IN) :: dQdTdA, elev                                                     ! input
       INTEGER, INTENT(IN) :: fault_LRi                                                       ! input
```

`src/MOD_Score.f90:2560`
```text
       LOGICAL locked, pureSS, sloped

!      DIMENSIONs of external argument arrays:
       DIMENSION alphaT(2), conduc(2), &
     &           continuum_LRi(mxEl), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
```

`src/MOD_Score.f90:2660`
```text
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * t_Biot)
                 thrust = dLEPdC * cGamma
                 normal = dLEPdC / cGamma
```

`src/MOD_Score.f90:2701`
```text
                 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
                 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
                 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
```

`src/MOD_Score.f90:2702`
```text

!                mean densities:
                 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
                 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
                 dLEPdZ(1) = gMean * (rho(1) - rhoH2O * t_Biot)
```

`src/MOD_SharedVars.f90:40`
```text
integer :: iConve,iPVRef,maxItr
character(len=2) :: pltRef

real*8 :: alphaT, conduc, constr, &
        & fFric, cFric, Biot, Byerly, aCreep, bCreep, cCreep, dCreep, eCreep, & ! default d_XXXX = LR_set_XXXX(0)
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
```

`src/MOD_SharedVars.f90:48`
```text
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
        & aCreep(2), bCreep(2), cCreep(2), dCreep(2), & ! default d_XXXX(1:2) = LR_set_XXXX(1:2, 0)
        & radio(2),  rhoBar(2), tauMax(2), temLim(2), &
		& omega(3, nPlate)
```

`src/MOD_ShellSet.f90:161`
```text
  & trim(VarNames(i)) /= 'trHMax' .AND. trim(VarNames(i)) /= 'tauMax' .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  & trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst' .AND. trim(VarNames(i)) /= 'gMean' .AND. &
  & trim(VarNames(i)) /= 'oneKm' .AND. trim(VarNames(i)) /= 'radius' .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  & trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  & trim(VarNames(i)) /= 'radio_C' .AND. trim(VarNames(i)) /= 'radio_M' .AND. trim(VarNames(i)) /= 'tSurf' .AND. &
  & trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
```

`src/MOD_ShellSet.f90:162`
```text
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  & trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst' .AND. trim(VarNames(i)) /= 'gMean' .AND. &
  & trim(VarNames(i)) /= 'oneKm' .AND. trim(VarNames(i)) /= 'radius' .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  & trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  & trim(VarNames(i)) /= 'radio_C' .AND. trim(VarNames(i)) /= 'radio_M' .AND. trim(VarNames(i)) /= 'tSurf' .AND. &
  & trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
```

`src/MOD_ShellSet.f90:233`
```text
  &  trim(VarNames(i)) /= 'trHMax'   .AND. trim(VarNames(i)) /= 'tauMax'   .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  &  trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst'   .AND. trim(VarNames(i)) /= 'gMean'    .AND. &
  &  trim(VarNames(i)) /= 'oneKm'    .AND. trim(VarNames(i)) /= 'radius'   .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  &  trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  &  trim(VarNames(i)) /= 'radio_C'  .AND. trim(VarNames(i)) /= 'radio_M'  .AND. trim(VarNames(i)) /= 'tSurf'    .AND. &
  &  trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
```

`src/MOD_ShellSet.f90:234`
```text
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  &  trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst'   .AND. trim(VarNames(i)) /= 'gMean'    .AND. &
  &  trim(VarNames(i)) /= 'oneKm'    .AND. trim(VarNames(i)) /= 'radius'   .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  &  trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  &  trim(VarNames(i)) /= 'radio_C'  .AND. trim(VarNames(i)) /= 'radio_M'  .AND. trim(VarNames(i)) /= 'tSurf'    .AND. &
  &  trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
```

`src/MOD_ShellSet.f90:558`
```text
      frmt = trim(frmt)//"X,F10.5,"
    case('radius')
      frmt = trim(frmt)//"X,F15.5,"
    case('alphaT_C')
      frmt = trim(frmt)//"X,ES12.5,"
    case('alphaT_M')
      frmt = trim(frmt)//"X,ES12.5,"
```

`src/MOD_ShellSet.f90:560`
```text
      frmt = trim(frmt)//"X,F15.5,"
    case('alphaT_C')
      frmt = trim(frmt)//"X,ES12.5,"
    case('alphaT_M')
      frmt = trim(frmt)//"X,ES12.5,"
    case('conduc_C')
      frmt = trim(frmt)//"X,F11.5,"
```

`src/MOD_ShellSet.f90:1065`
```text
  if(trim(VarNames(i)) == 'rhoBar_C') OData = .True.
  if(trim(VarNames(i)) == 'rhoBar_M') OData = .True.
  if(trim(VarNames(i)) == 'rhoAst')   OData = .True.
  if(trim(VarNames(i)) == 'alphaT_C') OData = .True.
  if(trim(VarNames(i)) == 'alphaT_M') OData = .True.
  if(trim(VarNames(i)) == 'conduc_C') OData = .True.
  if(trim(VarNames(i)) == 'conduc_M') OData = .True.
```

`src/MOD_ShellSet.f90:1066`
```text
  if(trim(VarNames(i)) == 'rhoBar_M') OData = .True.
  if(trim(VarNames(i)) == 'rhoAst')   OData = .True.
  if(trim(VarNames(i)) == 'alphaT_C') OData = .True.
  if(trim(VarNames(i)) == 'alphaT_M') OData = .True.
  if(trim(VarNames(i)) == 'conduc_C') OData = .True.
  if(trim(VarNames(i)) == 'conduc_M') OData = .True.
  if(trim(VarNames(i)) == 'radio_C')  OData = .True.
```

`src/MOD_ShellSet.f90:1084`
```text
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
```

`src/MOD_ShellSet.f90:1087`
```text
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
```

`src/MOD_ShellSet.f90:1156`
```text
      oneKm  = VarValues(i)
    case('radius')
      radius = VarValues(i)
    case('alphaT_C')
      alphaT(1) = VarValues(i)
    case('alphaT_M')
      alphaT(2) = VarValues(i)
```

`src/MOD_ShellSet.f90:1157`
```text
    case('radius')
      radius = VarValues(i)
    case('alphaT_C')
      alphaT(1) = VarValues(i)
    case('alphaT_M')
      alphaT(2) = VarValues(i)
    case('conduc_C')
```

`src/MOD_ShellSet.f90:1158`
```text
      radius = VarValues(i)
    case('alphaT_C')
      alphaT(1) = VarValues(i)
    case('alphaT_M')
      alphaT(2) = VarValues(i)
    case('conduc_C')
      conduc(1) = VarValues(i)
```

`src/MOD_ShellSet.f90:1159`
```text
    case('alphaT_C')
      alphaT(1) = VarValues(i)
    case('alphaT_M')
      alphaT(2) = VarValues(i)
    case('conduc_C')
      conduc(1) = VarValues(i)
    case('conduc_M')
```

`src/MOD_ShellSet.f90:1186`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
```

`src/MOD_ShellSet.f90:1188`
```text
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
```

`src/MOD_ShellSet.f90:1220`
```text
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
end do	

```

`src/MOD_ShellSet.f90:2419`
```text
!------------------------------------------------------------------------------

SUBROUTINE ReadPm (iUnit7, iUnitT, names , numPlt, offMax, & ! Read parameter input file
&                    aCreep, alphaT, bCreep, Biot  , &         ! output
&                    Byerly, cCreep, cFric , conduc, &
&                    dCreep, eCreep, everyP, fFric , gMean , &
&                    gradie, iConve, iPVRef, &
```

`src/MOD_ShellSet.f90:2438`
```text
       CHARACTER*2, INTENT(IN) :: names                                                       ! input
       INTEGER, INTENT(IN) :: numPlt                                                          ! input
       REAL*8, INTENT(IN) :: offMax                                                           ! input
       REAL*8, INTENT(OUT) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric , conduc, & ! output
          & dCreep, eCreep                                                                    ! output
       LOGICAL, INTENT(OUT) :: everyP                                                         ! output
       REAL*8, INTENT(OUT) :: fFric , gMean , gradie                                          ! output
```

`src/MOD_ShellSet.f90:2451`
```text
       CHARACTER*2,intent(out) :: pltRef
       INTEGER i, ios
       REAL*8 tempV, vector
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), names(numplt), radio(2), &
     &           rhoBar(2), tauMax(2), temLim(2), tempv(2), vector(2)

```

`src/MOD_ShellSet.f90:2739`
```text
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             alphaT)              ! output
       IF(Verbose) WRITE (iUnitT, 160) alphaT(1), alphaT(2)
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
```

`src/MOD_ShellSet.f90:2740`
```text

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             alphaT)              ! output
       IF(Verbose) WRITE (iUnitT, 160) alphaT(1), alphaT(2)
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
```

`src/MOD_ShellSet.f90:2741`
```text
       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             alphaT)              ! output
       IF(Verbose) WRITE (iUnitT, 160) alphaT(1), alphaT(2)
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
       IF ((alphaT(1) < 0.0D0).OR.(alphaT(2) < 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2744`
```text
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
       IF ((alphaT(1) < 0.0D0).OR.(alphaT(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative alphaT in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2745`
```text
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
       IF ((alphaT(1) < 0.0D0).OR.(alphaT(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative alphaT in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_Shells.f90:532`
```text
RETURN
END FUNCTION ATan2F

SUBROUTINE Balanc (alphaT, area, conduc, constr, &         ! input
&                    density_anomaly, detJ, dQdTdA, dXS, &
&                    dXSP, dYS, dYSP, edgeTS, elev, eta, &
&                    fArg, fC, fDip, &
```

`src/MOD_Shells.f90:589`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area, conduc, constr, density_anomaly, detJ, &      ! input
				   & dQdTdA, dXS, dXSP, dYS, dYSP                                ! input
LOGICAL, INTENT(IN) :: edgeTS                                                     ! input
REAL*8, INTENT(IN) :: elev, eta, &                                                ! input
```

`src/MOD_Shells.f90:632`
```text

DIMENSION points(3, 7), weight(7)
DIMENSION fPhi(4, 7), fPoint(7), fGauss(7)
DIMENSION area(mxEl), alphaT(2), &
&           comp(6, mxDOF), conduc(2), density_anomaly(mxNode), &
&           detJ(7, mxEl), dQdTdA(mxNode), &
&           dXS(2, 2, 3, 7, mxEl), dXSP(3, 7, mxEl), &
```

`src/MOD_Shells.f90:762`
```text
doFB2 = .FALSE.
doFB3 = .FALSE.
doFB4 = .TRUE.
CALL Fixed (alphaT, area, conduc, &  ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
```

`src/MOD_Shells.f90:886`
```text
doFB2 = .TRUE.
doFB3 = .FALSE.
doFB4 = .FALSE.
CALL Fixed (alphaT, area, conduc, &   ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
```

`src/MOD_Shells.f90:2250`
```text
RETURN
END SUBROUTINE Deriv

SUBROUTINE Diamnd (aCreep, alphaT, bCreep, & ! input
&                    Biot, cCreep, dCreep, &
&                    eCreep, &
&                    e1, e2, fric, g, &
```

`src/MOD_Shells.f90:2299`
```text
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
!      Arguments (*** all are scalars, even though
!      these same names may be arrays in other programs! ***):
REAL*8, INTENT(IN) :: aCreep, alphaT, bCreep, Biot, cCreep, dCreep, &                   ! input
&      eCreep, e1, e2, fric, g, &                                                         ! input
&      geoth1, geoth2, geoth3, geoth4, &                                                  ! input
&      pl0, pw0, &                                                                        ! input
```

`src/MOD_Shells.f90:2505`
```text
&        0.50D0 * geoth2 * z1 + &
&      0.3330D0 * geoth3 * z1**2 + &
&       0.250D0 * geoth4 * z1**3
	rhoUse = rhoBar * (1.0D0 - alphaT * tMean)
	sf1 = sf0 + dSFdEV * (rhoUse - Biot * rhoH2O) * g * thick
	t1 = MIN(temLim, geoth1 + geoth2 * z1 + geoth3 * z1**2 + geoth4 * z1**3)
	argume = (bCreep + cCreep * (zOfTop + z1)) / t1
```

`src/MOD_Shells.f90:2534`
```text
		 DO 100 n = 1, 7
			  zh = 0.50D0 * (z0 + z1)
			  tMean = 0.50D0 * (t0 + t1)
			  rhoUse = rhoBar * (1.0D0 - alphaT * tMean)
			  sfh = sf0 + dSFdEV * (rhoUse - Biot * rhoH2O) * g * (zh - z0)
			  th = MIN(temLim, geoth1 + geoth2 * zh + geoth3 * zh**2 + &
&                              geoth4 * zh**3)
```

`src/MOD_Shells.f90:2590`
```text
&        0.5D0 * geoth2 * (zTran / 2.0D0) + &
&      0.333D0 * geoth3 * (zTran / 2.0D0)**2 + &
&       0.25D0 * geoth4 * (zTran / 2.0D0)**3
	rhoUse = rhoBar * (1.0D0 - alphaT * tMean)
	sz = -pl0 - rhoUse * g * zTran / 2.0D0
	pH2O = pw0 + rhoH2O * g * zTran / 2.0D0
	szEff = sz + Biot * pH2O
```

`src/MOD_Shells.f90:3725`
```text
RETURN
END SUBROUTINE FEM

SUBROUTINE FillIn (alphaT, basal, conduc, &                  ! input
&                    continuum_LRi, &
&                    cooling_curvature, &
&                    density_anomaly, &
```

`src/MOD_Shells.f90:3749`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT                                                           ! input
DOUBLE PRECISION, INTENT(IN) :: basal                                                  ! input
REAL*8, INTENT(IN) :: conduc                                                           ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
```

`src/MOD_Shells.f90:3782`
```text
REAL*8 baseT, delta_quadratic, difMag, dTdZC, dTdZM, &
	& geoth1, geoth2, geoth3, geoth4, geoth5, geoth6, geoth7, geoth8, &
	& huge, q, shrMag, tAsthK, test, terr0r, vtime2, z
DIMENSION alphaT(2), atNode(mxNode), &
&           basal(2, mxNode),  &
&           conduc(2), contin(7, mxEl), &
&           continuum_LRi(mxEl), &
```

`src/MOD_Shells.f90:3980`
```text
&           3.0D0 * geoth4 * zMNode(i)**2
	geoth6 = dTdZC * conduc(1) / conduc(2)
	geoth7 = -0.50D0 * radio(2) / conduc(2) - 0.50D0 * cooling_curvature(i)
	CALL Squeez (alphaT, density_anomaly(i), elev(i), &  ! input
&                   geoth1, geoth2, geoth3, geoth4, &
&                   geoth5, geoth6, geoth7, geoth8, &
&                   gMean, &
```

`src/MOD_Shells.f90:4180`
```text
RETURN
END SUBROUTINE FindPV

SUBROUTINE Fixed (alphaT, area, conduc, & ! input
&                   density_anomaly, detJ, &
&                   doFB1, doFB2, doFB3, doFB4, &
&                   dQdTdA, dXS, dYS, &
```

`src/MOD_Shells.f90:4203`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area, conduc, density_anomaly, detJ                      ! input
LOGICAL, INTENT(IN) :: doFB1, doFB2, doFB3, doFB4                                      ! input
REAL*8, INTENT(IN) :: dQdTdA, dXS, dYS, dXSP, dYSP                                     ! input
LOGICAL, INTENT(IN) :: edgeTS                                                          ! input
```

`src/MOD_Shells.f90:4235`
```text
	& tauzz, theta, tL, toSide, tzz, &
	& x, x0, x1, x2, xout, xta, y, y0, y1, y2, yout, yta, z, zA, zM, zta, zta1, zta2
DOUBLE PRECISION fp1, fp2
DIMENSION alphaT(2), conduc(2), &
&           radio(2),  rhoBar(2), temLim(2)
DIMENSION phi(2), points(3, 7), theta(2), weight(7)
DIMENSION area(mxEl), density_anomaly(mxNode), &
```

`src/MOD_Shells.f90:4513`
```text
								  geoth6 = (q - zm * radio(1)) / conduc(2)
								  geoth7 = -0.5D0 * radio(2) / conduc(2)
								  geoth8 = 0.0D0
								  CALL Squeez (alphaT, &      ! input
&                                                 delta_rho, &
&                                                 elevat, &
&                                                 geoth1, geoth2, &
```

`src/MOD_Shells.f90:5537`
```text

END SUBROUTINE Lookup

SUBROUTINE Mohr (alphaT, conduc, constr, &                 ! input
&                  continuum_LRi, &
&                  dQdTdA, elev, &
&                  fault_LRi, fDip, fMuMax, &
```

`src/MOD_Shells.f90:5599`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, conduc, constr                                           ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
REAL*8, INTENT(IN) :: dQdTdA, elev                                                     ! input
INTEGER, INTENT(IN) :: fault_LRi                                                       ! input
```

`src/MOD_Shells.f90:5643`
```text
LOGICAL locked, pureSS, sloped

!      DIMENSIONs of external argument arrays:
DIMENSION alphaT(2), conduc(2), &
&           continuum_LRi(mxEl), &
&           dQdTdA(mxNode), elev(mxNode), &
&           fault_LRi(mxFEl), &
```

`src/MOD_Shells.f90:5743`
```text
		 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
&                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
		 tMeanC = (tSurf + tTrans) / 2.0D0
		 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
		 dLEPdC = gMean * (rhoC - rhoH2O * t_Biot)
		 thrust = dLEPdC * cGamma
		 normal = dLEPdC / cGamma
```

`src/MOD_Shells.f90:5784`
```text
		 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
		 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
		 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
```

`src/MOD_Shells.f90:5785`
```text

!                mean densities:
		 rho(1) = rhoBar(1) * (1.0D0 - alphaT(1) * tMean(1))
		 rho(2) = rhoBar(2) * (1.0D0 - alphaT(2) * tMean(2))

!                derivitives of lithostatic effective pressure wrt depth
		 dLEPdZ(1) = gMean * (rho(1) - rhoH2O * t_Biot)
```

`src/MOD_Shells.f90:6472`
```text
RETURN
END SUBROUTINE PrintK

SUBROUTINE Pure (alphaT, area, &                       ! input
&                  basal, &
&                  conduc, constr, continuum_LRi, &
&                  delta_rho, detJ, dQdTdA, dXS, dYS, &
```

`src/MOD_Shells.f90:6503`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area                                                      ! input
DOUBLE PRECISION, INTENT(IN) :: basal                                                   ! input
REAL*8, INTENT(IN) :: conduc, constr                                                    ! input
INTEGER, INTENT(IN) :: continuum_LRi                                                    ! input
```

### `conduc`

`INPUT/iEarth5-049.in:24`
```text
1000.           oneKm  = length of 1 kilometer, expressed in current length units (e.g., 1000. meters if using SI units)
6371000.        radius = mean radius of the planet, in m (if using SI units) (e.g., 6371000. for Earth)
2.4E-5,3.94E-5  alphaT = volumetric thermal expansion coefficients, in /C or /K, crust/mantle
2.7,3.20        conduc = thermal conductivity, crust/mantle (for SI units, in W/m/C)
3.5E-7,3.2E-8   radio = volumetric radioactive heat production (for SI units, in W/m**3)
273.            tSurf = surface temperature of planet, in K
1223.,1673.     temLim = temperature limits (due to melting) in crust/mantle-lithosphere, in Kelvin(!)
```

`src/MOD_Data.f90:210`
```text
       END SUBROUTINE Squeez

       SUBROUTINE Assign (aArray,    aX1,    aDX,    aX2,    nAX,    aDY,    aY2,    nAY, & ! INTENT(IN)
     &                    alphaT, cLimit, conduc, &                                         ! INTENT(IN)
     &                    cArray,    cX1,    cDX,    cX2,    nCX,    cDY,    cY2,    nCY, & ! INTENT(IN)
     &                    delta_rho_limit, &                                                ! INTENT(IN)
     &                    eArray,    eX1,    eDX,    eX2,    nEX,    eDY,    eY2,    nEY, & ! INTENT(IN)
```

`src/MOD_Data.f90:257`
```text
!   syntax revision to Fortran 90 by Peter Bird, UCLA, December 2018.
       IMPLICIT NONE
       REAL*8, INTENT(IN) :: aArray,    aX1,    aDX,    aX2,    aDY,    aY2, &
                           & alphaT, cLimit, conduc, &
                           & cArray,    cX1,    cDX,    cX2,    cDY,    cY2, &
                           & delta_rho_limit, &
                           & eArray,    eX1,    eDX,    eX2,    eDY,    eY2, &
```

`src/MOD_Data.f90:279`
```text
        !Argument arrays ALLOCATED and dimensioned in calling program:
        DIMENSION aArray(:, :), cArray(:, :), eArray(:, :), qArray(:, :), sArray(:, :)
        !Argument arrays with (crust:mantle) values:
        DIMENSION alphaT(2), conduc(2), radio(2), rhoBar(2), temLim(2)
!---------------------------------------------------------------------
        !Internal variables:
        INTEGER :: ic1, ic2, ir1, ir2
```

`src/MOD_Data.f90:516`
```text
            END IF

!        (2)Find total lithosphere thickness expected according to
!           a steady-state conduction model (like old OrbData; see
!           spreadsheet S20RTS_delta_ts_vs_age.xls for calibration).

            q_gdh1 = MAX(q_gdh1, qLimit)
```

`src/MOD_Data.f90:523`
```text
            q_gdh1 = MIN(q_gdh1, qLim1)
            q_radioactivity = 0.007D0
            delta_T = TAsthK - TSurf
            h_Earth3 = (delta_T * conduc(2)) / (q_gdh1 - q_radioactivity)

!        (3)Take geometric mean of this "Earth3" or "old OrbData"
!           thickness with the constant plate thickness of Stein &
```

`src/MOD_Data.f90:609`
```text
!   Compute steady-state GEOTHerm, as in old OrbData:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = -radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
```

`src/MOD_Data.f90:610`
```text

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = -radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
```

`src/MOD_Data.f90:615`
```text
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1)
       geoth6 = qRed / conduc(2)
       geoth7 = -radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0

```

`src/MOD_Data.f90:616`
```text
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1)
       geoth6 = qRed / conduc(2)
       geoth7 = -radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0

!   Check for Moho hotter than asthenosphere, and
```

`src/MOD_Data.f90:628`
```text
       test = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       IF (test > TAsthK) THEN
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
```

`src/MOD_Data.f90:633`
```text
            qLimit = qLim0 + dQL_dE * elevat
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
            qRed = heatFl - thickC * radio(1)
```

`src/MOD_Data.f90:637`
```text
            TMoho = TAsthK
            geoth5 = TMoho
            qRed = heatFl - thickC * radio(1)
            geoth6 = qRed / conduc(2)
       END IF

!   Compute trial value of cooling_curvature
```

`src/MOD_Data.f90:658`
```text

       IF (cooling_curvature > 0.0D0) THEN
            t_geoth1 = TSurf
            t_geoth2 = heatFl / conduc(1)
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
```

`src/MOD_Data.f90:659`
```text
       IF (cooling_curvature > 0.0D0) THEN
            t_geoth1 = TSurf
            t_geoth2 = heatFl / conduc(1)
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
            t_qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
```

`src/MOD_Data.f90:662`
```text
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
            t_qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
            t_geoth6 = qRed / conduc(2)
            t_geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))

```

`src/MOD_Data.f90:663`
```text
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
            t_geoth5 = t_TMoho
            t_qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
            t_geoth6 = qRed / conduc(2)
            t_geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))

!           Check for temperature maximum within mantle lithosphere:
```

`src/MOD_Data.f90:664`
```text
            t_geoth5 = t_TMoho
            t_qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
            t_geoth6 = qRed / conduc(2)
            t_geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))

!           Check for temperature maximum within mantle lithosphere:
            c0_of_mantle_gradient = t_geoth6
```

`src/MOD_Data.f90:692`
```text
!   Build geotherm again with final cooling_curvature:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
```

`src/MOD_Data.f90:693`
```text

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
```

`src/MOD_Data.f90:697`
```text
       geoth4 = 0.0D0
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
       geoth6 = qRed / conduc(2)
       geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0
```

`src/MOD_Data.f90:698`
```text
       TMoho = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
       geoth6 = qRed / conduc(2)
       geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0

```

`src/MOD_Data.f90:699`
```text
       geoth5 = TMoho
       qRed = heatFl - thickC * radio(1) - cooling_curvature * thickC * conduc(2)
       geoth6 = qRed / conduc(2)
       geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))
       geoth8 = 0.0D0

       chemical_delta_rho = 0.0D0
```

`src/MOD_Score.f90:1915`
```text


       SUBROUTINE OLDMohr (aCreep, alphaT, bCreep, Biot, Byerly, & ! input
     &                  cCreep, cFric, conduc, constr, dCreep, dQdTdA, &
     &                  eCreep, elev, fDip, fFric, fMuMax, &
     &                  fPFlt, fArg, gMean, &
     &                  mxFEl, mxNode, nFl, nodeF, &
```

`src/MOD_Score.f90:1973`
```text

       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric, conduc, &   ! input
          & constr, dCreep, dQdTdA, eCreep, elev, fDip, fFric, fMuMax, &                      ! input
          & fPFlt, fArg, gMean                                                                ! input
       INTEGER, INTENT(IN) :: mxFEl, mxNode, nFl, nodeF                                       ! input
```

`src/MOD_Score.f90:2014`
```text
!      DIMENSIONs of internal convenience arrays:
       DIMENSION dLEPdZ(2), dSFdZ(2), rho(2), sheart(2), tMean(2), zTrans(2)
!      DIMENSIONs of external argument arrays:
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), dQdTdA(mxNode), elev(mxNode), &
     &           fC(2, 2, 7, mxFEl), fDip(2, mxFEl), &
     &           fIMuDZ(7, mxFEl), fPeakS(2, mxFEl), &
```

`src/MOD_Score.f90:2090`
```text
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
```

`src/MOD_Score.f90:2091`
```text
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * Biot)
```

`src/MOD_Score.f90:2122`
```text
                 mantle = MAX(mantle, 0.0D0)

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
```

`src/MOD_Score.f90:2123`
```text

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
```

`src/MOD_Score.f90:2126`
```text
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
```

`src/MOD_Score.f90:2127`
```text

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
                 tMean(1) = (tSurf + tMoho) / 2.0D0
```

`src/MOD_Score.f90:2254`
```text
                           zAbs = z + z0
                           shearf = z * dSFdZ(layer) + sf0
                           shearp = MIN(shearf, dCreep(layer))
                           t = t0 + q0 * z / conduc(layer) - (radio(layer) / &
     &                                          (2.0D0 * conduc(layer))) * z**2
                           IF (zAbs <= (15.0D0 * oneKm)) THEN
                                t90pc = 0.50D0 * zAbs
```

`src/MOD_Score.f90:2255`
```text
                           shearf = z * dSFdZ(layer) + sf0
                           shearp = MIN(shearf, dCreep(layer))
                           t = t0 + q0 * z / conduc(layer) - (radio(layer) / &
     &                                          (2.0D0 * conduc(layer))) * z**2
                           IF (zAbs <= (15.0D0 * oneKm)) THEN
                                t90pc = 0.50D0 * zAbs
                           ELSE IF (zAbs < (45.0D0 * oneKm)) THEN
```

`src/MOD_Score.f90:2325`
```text
                           zfull = z0 + dz
                           azhalf = zhalf + zAbs
                           azfull = zfull + zAbs
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
```

`src/MOD_Score.f90:2327`
```text
                           azfull = zfull + zAbs
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
```

`src/MOD_Score.f90:2328`
```text
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
                           IF (azhalf <= (15.0D0 * oneKm)) THEN
```

`src/MOD_Score.f90:2330`
```text
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
                           IF (azhalf <= (15.0D0 * oneKm)) THEN
                                whalf = 0.50D0 * azhalf
                           ELSE IF (azhalf < (45.0D0 * oneKm)) THEN
```

`src/MOD_Score.f90:2454`
```text
       END SUBROUTINE OLDMohr


       SUBROUTINE Mohr (alphaT, conduc, constr, &                 ! input
     &                  continuum_LRi, &
     &                  dQdTdA, elev, &
     &                  fault_LRi, fDip, fMuMax, &
```

`src/MOD_Score.f90:2516`
```text

       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       REAL*8, INTENT(IN) :: alphaT, conduc, constr                                           ! input
       INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
       REAL*8, INTENT(IN) :: dQdTdA, elev                                                     ! input
       INTEGER, INTENT(IN) :: fault_LRi                                                       ! input
```

`src/MOD_Score.f90:2560`
```text
       LOGICAL locked, pureSS, sloped

!      DIMENSIONs of external argument arrays:
       DIMENSION alphaT(2), conduc(2), &
     &           continuum_LRi(mxEl), &
     &           dQdTdA(mxNode), elev(mxNode), &
     &           fault_LRi(mxFEl), &
```

`src/MOD_Score.f90:2657`
```text
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
```

`src/MOD_Score.f90:2658`
```text
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * t_Biot)
```

`src/MOD_Score.f90:2689`
```text
                 mantle = MAX(mantle, 0.0D0)

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
```

`src/MOD_Score.f90:2690`
```text

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
```

`src/MOD_Score.f90:2693`
```text
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
```

`src/MOD_Score.f90:2694`
```text

!                Temperature at base of plate:
                 tAsth = tMoho + mantle * (q - crust * radio(1)) / conduc(2) - &
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
                 tMean(1) = (tSurf + tMoho) / 2.0D0
```

`src/MOD_Score.f90:2821`
```text
                           zAbs = z + z0
                           shearf = z * dSFdZ(layer) + sf0
                           shearp = MIN(shearf, t_dCreep(layer))
                           t = t0 + q0 * z / conduc(layer) - (radio(layer) / &
     &                                          (2.0D0 * conduc(layer))) * z**2
                           IF (zAbs <= (15.0D0 * oneKm)) THEN
                                t90pc = 0.50D0 * zAbs
```

`src/MOD_Score.f90:2822`
```text
                           shearf = z * dSFdZ(layer) + sf0
                           shearp = MIN(shearf, t_dCreep(layer))
                           t = t0 + q0 * z / conduc(layer) - (radio(layer) / &
     &                                          (2.0D0 * conduc(layer))) * z**2
                           IF (zAbs <= (15.0D0 * oneKm)) THEN
                                t90pc = 0.50D0 * zAbs
                           ELSE IF (zAbs < (45.0D0 * oneKm)) THEN
```

`src/MOD_Score.f90:2892`
```text
                           zfull = z0 + dz
                           azhalf = zhalf + zAbs
                           azfull = zfull + zAbs
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
```

`src/MOD_Score.f90:2894`
```text
                           azfull = zfull + zAbs
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
```

`src/MOD_Score.f90:2895`
```text
                           thalf = t0 + q0 * zhalf / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
                           IF (azhalf <= (15.0D0 * oneKm)) THEN
```

`src/MOD_Score.f90:2897`
```text
     &                          (2.0D0 * conduc(layer))) * zhalf**2
                           tfull = t0 + q0 * zfull / conduc(layer) - &
     &                          (radio(layer) / &
     &                          (2.0D0 * conduc(layer))) * zfull**2
                           IF (azhalf <= (15.0D0 * oneKm)) THEN
                                whalf = 0.50D0 * azhalf
                           ELSE IF (azhalf < (45.0D0 * oneKm)) THEN
```

`src/MOD_SharedVars.f90:40`
```text
integer :: iConve,iPVRef,maxItr
character(len=2) :: pltRef

real*8 :: alphaT, conduc, constr, &
        & fFric, cFric, Biot, Byerly, aCreep, bCreep, cCreep, dCreep, eCreep, & ! default d_XXXX = LR_set_XXXX(0)
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
```

`src/MOD_SharedVars.f90:48`
```text
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
        & aCreep(2), bCreep(2), cCreep(2), dCreep(2), & ! default d_XXXX(1:2) = LR_set_XXXX(1:2, 0)
        & radio(2),  rhoBar(2), tauMax(2), temLim(2), &
		& omega(3, nPlate)
```

`src/MOD_ShellSet.f90:162`
```text
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  & trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst' .AND. trim(VarNames(i)) /= 'gMean' .AND. &
  & trim(VarNames(i)) /= 'oneKm' .AND. trim(VarNames(i)) /= 'radius' .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  & trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  & trim(VarNames(i)) /= 'radio_C' .AND. trim(VarNames(i)) /= 'radio_M' .AND. trim(VarNames(i)) /= 'tSurf' .AND. &
  & trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
```

`src/MOD_ShellSet.f90:234`
```text
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  &  trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst'   .AND. trim(VarNames(i)) /= 'gMean'    .AND. &
  &  trim(VarNames(i)) /= 'oneKm'    .AND. trim(VarNames(i)) /= 'radius'   .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  &  trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  &  trim(VarNames(i)) /= 'radio_C'  .AND. trim(VarNames(i)) /= 'radio_M'  .AND. trim(VarNames(i)) /= 'tSurf'    .AND. &
  &  trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
```

`src/MOD_ShellSet.f90:562`
```text
      frmt = trim(frmt)//"X,ES12.5,"
    case('alphaT_M')
      frmt = trim(frmt)//"X,ES12.5,"
    case('conduc_C')
      frmt = trim(frmt)//"X,F11.5,"
    case('conduc_M')
      frmt = trim(frmt)//"X,F11.5,"
```

`src/MOD_ShellSet.f90:564`
```text
      frmt = trim(frmt)//"X,ES12.5,"
    case('conduc_C')
      frmt = trim(frmt)//"X,F11.5,"
    case('conduc_M')
      frmt = trim(frmt)//"X,F11.5,"
    case('radio_C')
      frmt = trim(frmt)//"X,ES12.5,"
```

`src/MOD_ShellSet.f90:1067`
```text
  if(trim(VarNames(i)) == 'rhoAst')   OData = .True.
  if(trim(VarNames(i)) == 'alphaT_C') OData = .True.
  if(trim(VarNames(i)) == 'alphaT_M') OData = .True.
  if(trim(VarNames(i)) == 'conduc_C') OData = .True.
  if(trim(VarNames(i)) == 'conduc_M') OData = .True.
  if(trim(VarNames(i)) == 'radio_C')  OData = .True.
  if(trim(VarNames(i)) == 'radio_M')  OData = .True.
```

`src/MOD_ShellSet.f90:1068`
```text
  if(trim(VarNames(i)) == 'alphaT_C') OData = .True.
  if(trim(VarNames(i)) == 'alphaT_M') OData = .True.
  if(trim(VarNames(i)) == 'conduc_C') OData = .True.
  if(trim(VarNames(i)) == 'conduc_M') OData = .True.
  if(trim(VarNames(i)) == 'radio_C')  OData = .True.
  if(trim(VarNames(i)) == 'radio_M')  OData = .True.
  if(trim(VarNames(i)) == 'tSurf')    OData = .True.
```

`src/MOD_ShellSet.f90:1084`
```text
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
```

`src/MOD_ShellSet.f90:1087`
```text
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
```

`src/MOD_ShellSet.f90:1160`
```text
      alphaT(1) = VarValues(i)
    case('alphaT_M')
      alphaT(2) = VarValues(i)
    case('conduc_C')
      conduc(1) = VarValues(i)
    case('conduc_M')
      conduc(2) = VarValues(i)
```

`src/MOD_ShellSet.f90:1161`
```text
    case('alphaT_M')
      alphaT(2) = VarValues(i)
    case('conduc_C')
      conduc(1) = VarValues(i)
    case('conduc_M')
      conduc(2) = VarValues(i)
    case('radio_C')
```

`src/MOD_ShellSet.f90:1162`
```text
      alphaT(2) = VarValues(i)
    case('conduc_C')
      conduc(1) = VarValues(i)
    case('conduc_M')
      conduc(2) = VarValues(i)
    case('radio_C')
      radio(1) = VarValues(i)
```

`src/MOD_ShellSet.f90:1163`
```text
    case('conduc_C')
      conduc(1) = VarValues(i)
    case('conduc_M')
      conduc(2) = VarValues(i)
    case('radio_C')
      radio(1) = VarValues(i)
    case('radio_M')
```

`src/MOD_ShellSet.f90:1186`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
```

`src/MOD_ShellSet.f90:1188`
```text
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
```

`src/MOD_ShellSet.f90:1220`
```text
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
end do	

```

`src/MOD_ShellSet.f90:2420`
```text

SUBROUTINE ReadPm (iUnit7, iUnitT, names , numPlt, offMax, & ! Read parameter input file
&                    aCreep, alphaT, bCreep, Biot  , &         ! output
&                    Byerly, cCreep, cFric , conduc, &
&                    dCreep, eCreep, everyP, fFric , gMean , &
&                    gradie, iConve, iPVRef, &
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
```

`src/MOD_ShellSet.f90:2438`
```text
       CHARACTER*2, INTENT(IN) :: names                                                       ! input
       INTEGER, INTENT(IN) :: numPlt                                                          ! input
       REAL*8, INTENT(IN) :: offMax                                                           ! input
       REAL*8, INTENT(OUT) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric , conduc, & ! output
          & dCreep, eCreep                                                                    ! output
       LOGICAL, INTENT(OUT) :: everyP                                                         ! output
       REAL*8, INTENT(OUT) :: fFric , gMean , gradie                                          ! output
```

`src/MOD_ShellSet.f90:2451`
```text
       CHARACTER*2,intent(out) :: pltRef
       INTEGER i, ios
       REAL*8 tempV, vector
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), names(numplt), radio(2), &
     &           rhoBar(2), tauMax(2), temLim(2), tempv(2), vector(2)

```

`src/MOD_ShellSet.f90:2750`
```text
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             conduc)              ! output
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
```

`src/MOD_ShellSet.f90:2751`
```text

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             conduc)              ! output
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2752`
```text
       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             conduc)              ! output
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
```

`src/MOD_ShellSet.f90:2754`
```text
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2755`
```text
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_Shells.f90:532`
```text
RETURN
END FUNCTION ATan2F

SUBROUTINE Balanc (alphaT, area, conduc, constr, &         ! input
&                    density_anomaly, detJ, dQdTdA, dXS, &
&                    dXSP, dYS, dYSP, edgeTS, elev, eta, &
&                    fArg, fC, fDip, &
```

`src/MOD_Shells.f90:589`
```text

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8, INTENT(IN) :: alphaT, area, conduc, constr, density_anomaly, detJ, &      ! input
				   & dQdTdA, dXS, dXSP, dYS, dYSP                                ! input
LOGICAL, INTENT(IN) :: edgeTS                                                     ! input
REAL*8, INTENT(IN) :: elev, eta, &                                                ! input
```

### `TSurf`

`INPUT/iEarth5-049.in:26`
```text
2.4E-5,3.94E-5  alphaT = volumetric thermal expansion coefficients, in /C or /K, crust/mantle
2.7,3.20        conduc = thermal conductivity, crust/mantle (for SI units, in W/m/C)
3.5E-7,3.2E-8   radio = volumetric radioactive heat production (for SI units, in W/m**3)
273.            tSurf = surface temperature of planet, in K
1223.,1673.     temLim = temperature limits (due to melting) in crust/mantle-lithosphere, in Kelvin(!)
50              maxItr = maximum number of iterations of the velocity solution (e.g., 80?)
0.0005          okToQt = acceptable level of fractional change in RMS velocity which stops iteration
```

`src/MOD_Data.f90:222`
```text
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                    TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                    elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                    thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                    arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

`src/MOD_Data.f90:268`
```text
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
                           & TAsthK, temLim,  TSurf
       INTEGER, INTENT(IN) ::    nAX,    nAY,    nCX,    nCY,    nEX,    nEY, &
                            & iUnitL, iUnitT, &
                            &    nQX,    nQY,    nSX,    nSY
```

`src/MOD_Data.f90:522`
```text
            q_gdh1 = MAX(q_gdh1, qLimit)
            q_gdh1 = MIN(q_gdh1, qLim1)
            q_radioactivity = 0.007D0
            delta_T = TAsthK - TSurf
            h_Earth3 = (delta_T * conduc(2)) / (q_gdh1 - q_radioactivity)

!        (3)Take geometric mean of this "Earth3" or "old OrbData"
```

`src/MOD_Data.f90:608`
```text

!   Compute steady-state GEOTHerm, as in old OrbData:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = -radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
```

`src/MOD_Data.f90:657`
```text
!      maximum within the lithosphere (forbidden!)?:

       IF (cooling_curvature > 0.0D0) THEN
            t_geoth1 = TSurf
            t_geoth2 = heatFl / conduc(1)
            t_geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
            t_TMoho = t_geoth1 + t_geoth2 * thickC + t_geoth3 * thickC**2
```

`src/MOD_Data.f90:691`
```text

!   Build geotherm again with final cooling_curvature:

       geoth1 = TSurf
       geoth2 = heatFl / conduc(1)
       geoth3 = delta_quadratic - radio(1) / (2.0D0 * conduc(1))
       geoth4 = 0.0D0
```

`src/MOD_Score.f90:1922`
```text
     &                  offMax, offset, &
     &                  oneKm, radio, rhoH2O, rhoBar, &
     &                  slide, tauMax, &
     &                  tLNode, tSurf, v, wedge, &
     &                  zMNode, &
     &                  zTranF, &                               ! modify
     &                  fC, fIMuDZ, fPeakS, fSlips, fTStar)     ! output
```

`src/MOD_Score.f90:1978`
```text
          & fPFlt, fArg, gMean                                                                ! input
       INTEGER, INTENT(IN) :: mxFEl, mxNode, nFl, nodeF                                       ! input
       REAL*8, INTENT(IN) :: offMax, offset, oneKm, radio, rhoH2O, rhoBar, slide              ! input
       REAL*8, INTENT(IN) :: tauMax, tLNode, tSurf                                            ! input
       DOUBLE PRECISION, INTENT(IN) :: v                                                      ! input
       REAL*8, INTENT(IN) :: wedge, zMNode                                                    ! input
       REAL*8, INTENT(INOUT) :: zTranF                                                        ! modify
```

`src/MOD_Score.f90:2090`
```text
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
```

`src/MOD_Score.f90:2092`
```text
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2. * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * Biot)
                 thrust = dLEPdC * cGamma
```

`src/MOD_Score.f90:2122`
```text
                 mantle = MAX(mantle, 0.0D0)

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
```

`src/MOD_Score.f90:2130`
```text
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
                 tMean(1) = (tSurf + tMoho) / 2.0D0
                 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
```

`src/MOD_Score.f90:2239`
```text
                      IF (layer == 1) THEN
                           baseZ = crust
                           sf0 = 0.0D0
                           t0 = tSurf
                           q0 = q
                           z0 = 0.0D0
                      ELSE
```

`src/MOD_Score.f90:2307`
```text
                 DO 80 layer = 1, limit
                      IF (layer == 1) THEN
                           thick = crust
                           t0 = tSurf
                           q0 = q
                           zAbs = 0.0D0
                      ELSE
```

`src/MOD_Score.f90:2465`
```text
     &                  offMax, offset, &
     &                  oneKm, radio, rhoH2O, rhoBar, &
     &                  slide, tauMax, &
     &                  tLNode, tSurf, v, wedge, &
     &                  zMNode, &
     &                  zTranF, &                               ! modify
     &                  fC, fIMuDZ, fPeakS, fSlips, fTStar)     ! output
```

`src/MOD_Score.f90:2526`
```text
                           & LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep ! input
       INTEGER, INTENT(IN) :: mxEl, mxFEl, mxNode, nFl, nodeF                                 ! input
       REAL*8, INTENT(IN) :: offMax, offset, oneKm, radio, rhoH2O, rhoBar, slide              ! input
       REAL*8, INTENT(IN) :: tauMax, tLNode, tSurf                                            ! input
       DOUBLE PRECISION, INTENT(IN) :: v                                                      ! input
       REAL*8, INTENT(IN) :: wedge, zMNode                                                    ! input
       REAL*8, INTENT(INOUT) :: zTranF                                                        ! modify
```

`src/MOD_Score.f90:2657`
```text
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
```

`src/MOD_Score.f90:2659`
```text
     &                          dQdTdA(n3) + dQdTdA(n4))
                 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
     &                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
                 tMeanC = (tSurf + tTrans) / 2.0D0
                 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
                 dLEPdC = gMean * (rhoC - rhoH2O * t_Biot)
                 thrust = dLEPdC * cGamma
```

`src/MOD_Score.f90:2689`
```text
                 mantle = MAX(mantle, 0.0D0)

!                Moho temperature:
                 tMoho = tSurf + crust * q / conduc(1) - &
     &                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
```

`src/MOD_Score.f90:2697`
```text
     &                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
                 tMean(1) = (tSurf + tMoho) / 2.0D0
                 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
```

`src/MOD_Score.f90:2806`
```text
                      IF (layer == 1) THEN
                           baseZ = crust
                           sf0 = 0.0D0
                           t0 = tSurf
                           q0 = q
                           z0 = 0.0D0
                      ELSE
```

`src/MOD_Score.f90:2874`
```text
                 DO 80 layer = 1, limit
                      IF (layer == 1) THEN
                           thick = crust
                           t0 = tSurf
                           q0 = q
                           zAbs = 0.0D0
                      ELSE
```

`src/MOD_SharedVars.f90:45`
```text
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
        & radio, radius, refStr, rhoAst, rhoBar, rhoH2O, &
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
```

`src/MOD_ShellSet.f90:163`
```text
  & trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst' .AND. trim(VarNames(i)) /= 'gMean' .AND. &
  & trim(VarNames(i)) /= 'oneKm' .AND. trim(VarNames(i)) /= 'radius' .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  & trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  & trim(VarNames(i)) /= 'radio_C' .AND. trim(VarNames(i)) /= 'radio_M' .AND. trim(VarNames(i)) /= 'tSurf' .AND. &
  & trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
    Abort = .True.
```

`src/MOD_ShellSet.f90:235`
```text
  &  trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst'   .AND. trim(VarNames(i)) /= 'gMean'    .AND. &
  &  trim(VarNames(i)) /= 'oneKm'    .AND. trim(VarNames(i)) /= 'radius'   .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  &  trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  &  trim(VarNames(i)) /= 'radio_C'  .AND. trim(VarNames(i)) /= 'radio_M'  .AND. trim(VarNames(i)) /= 'tSurf'    .AND. &
  &  trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
    Abort = .True.
```

`src/MOD_ShellSet.f90:570`
```text
      frmt = trim(frmt)//"X,ES12.5,"
    case('radio_M')
      frmt = trim(frmt)//"X,ES12.5,"
    case('tSurf')
      frmt = trim(frmt)//"X,F11.5,"
    case('temLim_C')
      frmt = trim(frmt)//"X,F11.5,"
```

`src/MOD_ShellSet.f90:1071`
```text
  if(trim(VarNames(i)) == 'conduc_M') OData = .True.
  if(trim(VarNames(i)) == 'radio_C')  OData = .True.
  if(trim(VarNames(i)) == 'radio_M')  OData = .True.
  if(trim(VarNames(i)) == 'tSurf')    OData = .True.
  if(trim(VarNames(i)) == 'temLim_C') OData = .True.
  if(trim(VarNames(i)) == 'temLim_M') OData = .True.
  i = i+1
```

`src/MOD_ShellSet.f90:1084`
```text
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
```

`src/MOD_ShellSet.f90:1090`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(:),intent(in) :: VarNames
```

`src/MOD_ShellSet.f90:1168`
```text
      radio(1) = VarValues(i)
    case('radio_M')
      radio(2) = VarValues(i)
    case('tSurf')
      tSurf = VarValues(i)
    case('temLim_C')
      temLim(1) = VarValues(i)
```

`src/MOD_ShellSet.f90:1169`
```text
    case('radio_M')
      radio(2) = VarValues(i)
    case('tSurf')
      tSurf = VarValues(i)
    case('temLim_C')
      temLim(1) = VarValues(i)
    case('temLim_M')
```

`src/MOD_ShellSet.f90:1186`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
```

`src/MOD_ShellSet.f90:1191`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(1) :: UpName
```

`src/MOD_ShellSet.f90:1220`
```text
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
end do	

```

`src/MOD_ShellSet.f90:2426`
```text
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
&                    radius, refStr, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, tauMax, temLim, title3, &
&                    trHMax, tSurf,  vTimes, zBAsth, pltRef)



```

`src/MOD_ShellSet.f90:2446`
```text
       REAL*8, INTENT(OUT) :: okDelV, okToQt, oneKm,  radio, radius, refStr, &                ! output
          & rhoAst, rhoBar, rhoH2O, tAdiab, tauMax, temLim                                    ! output
       CHARACTER*100, INTENT(OUT) :: title3                                                    ! output
       REAL*8, INTENT(OUT) :: trHMax, tSurf,  vTimes, zBAsth                                  ! output
     ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       CHARACTER*2,intent(out) :: pltRef
       INTEGER i, ios
```

`src/MOD_ShellSet.f90:2769`
```text
          call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tSurf
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
```

`src/MOD_ShellSet.f90:2770`
```text
       END IF

       READ (iunit7, * ) tSurf
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
```

`src/MOD_ShellSet.f90:2771`
```text

       READ (iunit7, * ) tSurf
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
```

`src/MOD_ShellSet.f90:2773`
```text
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2774`
```text
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_Shells.f90:546`
```text
&                    sigZZI, sita, &
&                    tauMat, tauZZI, tauZZN, temLim, &
&                    title1, title2, title3, &
&                    tLNode, tSurf, v, wedge, xNode, yNode, zMNode, &
&                    sigHB, &                               ! modify
&                    comp, &                                ! output
&                    fBase, outVec)                         ! work
```

`src/MOD_Shells.f90:601`
```text
				   & sigZZI, sita, &                                             ! input
				   & tauMat, tauZZI, tauZZN, temLim                              ! input
CHARACTER*100, INTENT(IN) :: title1, title2, title3                                ! input
REAL*8, INTENT(IN) :: tLNode, tSurf                                               ! input
DOUBLE PRECISION, INTENT(IN) :: v                                                 ! input
REAL*8, INTENT(IN) :: wedge, xNode, yNode, zMNode                                 ! input
REAL*8, INTENT(INOUT) :: sigHB                                                    ! modify
```

`src/MOD_Shells.f90:773`
```text
&             nCond, nFl, nodCon, nodeF, nodes, numEl, &
&             oneKm, radio, radius, &
&             rhoAst, rhoBar, rhoH2O, sigZZI, &
&             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&             xNode, yNode, zMNode, &
&             fBase)                   ! output
DO 210 i = 1, nEntry
```

`src/MOD_Shells.f90:897`
```text
&             nCond, nFl, nodCon, nodeF, nodes, numEl, &
&             oneKm, radio, radius, &
&             rhoAst, rhoBar, rhoH2O, sigZZI, &
&             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&             xNode, yNode, zMNode, &
&             fBase)                   ! output
DO 310 i = 1, nEntry
```

`src/MOD_Shells.f90:3737`
```text
&                    names, nodes, &
&                    nPlate, numEl, numNod, omega, oneKm, &
&                    radio, radius, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, temLim, tLNode, trHMax, tSurf, &
&                    vTimes, whichP, xNode, yNode, zBAsth, &
&                    zMNode, &
&                    contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/MOD_Shells.f90:3762`
```text
CHARACTER*2, INTENT(IN) :: names                                                       ! input
INTEGER, INTENT(IN) :: nodes, nPlate, numEl, numNod                                    ! input
REAL*8, INTENT(IN) :: omega, oneKm, radio, radius, rhoAst, rhoBar, rhoH2O, &           ! input
				   & tAdiab, temLim, tLNode, trHMax, tSurf, vTimes                    ! input
INTEGER, INTENT(IN) :: whichP                                                          ! input
REAL*8, INTENT(IN) :: xNode, yNode                                                     ! input
REAL*8, INTENT(IN) :: zBAsth, zMNode                                                   ! input
```

`src/MOD_Shells.f90:3905`
```text

tAsthK = tAdiab + gradie * 100.0D3

geoth1 = tSurf
geoth3 = -0.5D0 * radio(1) / conduc(1)
geoth4 = 0.0D0
geoth7 = -0.5D0 * radio(2) / conduc(2)
```

`src/MOD_Shells.f90:4191`
```text
&                   nCond, nFl, nodCon, nodeF, nodes, numEl, &
&                   oneKm, radio, radius, rhoAst, &
&                   rhoBar, rhoH2O, sigZZI, sita, &
&                   tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&                   xNode, yNode, zMNode, &
&                   fBase)                  ! output

```

`src/MOD_Shells.f90:4211`
```text
INTEGER, INTENT(IN) :: iCond, iUnitT, mxBn, mxDOF, mxEl, mxFEl, mxNode, &              ! input
	 & nCond, nFl, nodCon, nodeF, nodes, numEl                                        ! input
REAL*8, INTENT(IN) :: oneKm, radio, radius, rhoAst, rhoBar, rhoH2O, sigZZI, sita, &    ! input
  & tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, xNode, yNode, zMNode                ! input
DOUBLE PRECISION, INTENT(OUT) :: fBase                                                 ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
DOUBLE PRECISION fPoint, fPhi, fGauss
```

`src/MOD_Shells.f90:4504`
```text
!                                             emerges into asthenosphere
!                                             anywhere along slant path:
								  IF (z > (zM + tL)) GO TO 251
								  geoth1 = tSurf
								  geoth2 = q / conduc(1)
								  geoth3 = -0.5D0 * radio(1) / conduc(1)
								  geoth4 = 0.0D0
```

`src/MOD_Shells.f90:5548`
```text
&                  offMax, offset, &
&                  oneKm, radio, rhoH2O, rhoBar, &
&                  slide, tauMax, &
&                  tLNode, tSurf, v, wedge, &
&                  zMNode, &
&                  zTranF, &                               ! modify
&                  fC, fIMuDZ, fPeakS, fSlips, fTStar)     ! output
```

`src/MOD_Shells.f90:5609`
```text
				   & LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep ! input
INTEGER, INTENT(IN) :: mxEl, mxFEl, mxNode, nFl, nodeF                                 ! input
REAL*8, INTENT(IN) :: offMax, offset, oneKm, radio, rhoH2O, rhoBar, slide              ! input
REAL*8, INTENT(IN) :: tauMax, tLNode, tSurf                                            ! input
DOUBLE PRECISION, INTENT(IN) :: v                                                      ! input
REAL*8, INTENT(IN) :: wedge, zMNode                                                    ! input
REAL*8, INTENT(INOUT) :: zTranF                                                        ! modify
```

`src/MOD_Shells.f90:5740`
```text
!                check that it lies within frictional limits of blocks:
		 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
&                          dQdTdA(n3) + dQdTdA(n4))
		 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
&                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
		 tMeanC = (tSurf + tTrans) / 2.0D0
		 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
```

`src/MOD_Shells.f90:5742`
```text
&                          dQdTdA(n3) + dQdTdA(n4))
		 tTrans = tSurf + zTranF(1, i) * q / conduc(1) - &
&                    zTranF(1, i)**2 * radio(1) / (2.0D0 * conduc(1))
		 tMeanC = (tSurf + tTrans) / 2.0D0
		 rhoC = rhoBar(1) * (1.0D0 - alphaT(1) * tMeanC)
		 dLEPdC = gMean * (rhoC - rhoH2O * t_Biot)
		 thrust = dLEPdC * cGamma
```

`src/MOD_Shells.f90:5772`
```text
		 mantle = MAX(mantle, 0.0D0)

!                Moho temperature:
		 tMoho = tSurf + crust * q / conduc(1) - &
&                       crust**2 * radio(1) / (2.0D0 * conduc(1))

!                Temperature at base of plate:
```

`src/MOD_Shells.f90:5780`
```text
&                       mantle**2 * radio(2) / (2.0D0 * conduc(2))

!                mean temperatures:
		 tMean(1) = (tSurf + tMoho) / 2.0D0
		 tMean(2) = (tMoho + tAsth) / 2.0D0

!                mean densities:
```

`src/MOD_Shells.f90:5889`
```text
			  IF (layer == 1) THEN
				   baseZ = crust
				   sf0 = 0.0D0
				   t0 = tSurf
				   q0 = q
				   z0 = 0.0D0
			  ELSE
```

`src/MOD_Shells.f90:5957`
```text
		 DO 80 layer = 1, limit
			  IF (layer == 1) THEN
				   thick = crust
				   t0 = tSurf
				   q0 = q
				   zAbs = 0.0D0
			  ELSE
```

`src/MOD_Shells.f90:6489`
```text
&                  radio, radius, rhoBar, rhoH2O, sita, slide, &
&                  tauMax, temLim, title1, &
&                  title2, title3, tLInt, tLNode, trHMax, &
&                  tSurf, vBCArg, vBCMag, visMax, wedge, &
&                  zMNode, zMoho, lastPm, &
&                  v, &                                  ! modify
&                  eRate, eta, fIMuDZ, fPeakS, fSlips, & ! output
```

`src/MOD_Shells.f90:6525`
```text
REAL*8, INTENT(IN) :: radio, radius, rhoBar, rhoH2O, sita, slide                        ! input
REAL*8, INTENT(IN) :: tauMax, temLim                                                    ! input
CHARACTER*100, INTENT(IN) :: title1, title2, title3                                      ! input
REAL*8, INTENT(IN) :: tLInt, tLNode, trHMax, tSurf, vBCArg, vBCMag, visMax, wedge, &    ! input
				   & zMNode, zMoho                                                     ! input
INTEGER, INTENT(IN) :: lastPm                                                           ! input
DOUBLE PRECISION, INTENT(INOUT) :: v                                                    ! modify
```

`src/MOD_Shells.f90:6640`
```text
&            offMax, offset, &
&            oneKm, radio, rhoH2O, rhoBar, &
&            slide, tauMax, &
&            tLNode, tSurf, v, wedge, &
&            zMNode, &
&            zTranF, &                             ! modify
&            fC, fIMuDZ, fPeakS, fSlips, fTStar)   ! output
```

`src/MOD_Shells.f90:6704`
```text
&                 offMax, offset, &
&                 oneKm, radio, rhoH2O, rhoBar, &
&                 slide, tauMax, &
&                 tLNode, tSurf, v, wedge, &
&                 zMNode, &
&                 zTranF, &                             ! modify
&                 fC, fIMuDZ, fPeakS, fSlips, fTStar)   ! output
```

`src/OrbData5.f90:539`
```text
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                   TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                   elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                   thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                   arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

`src/OrbScore2.f90:1067`
```text
         &            offMax, offset, &
         &            oneKm, radio, rhoH2O, rhoBar, &
         &            slide, tauMax, &
         &            tLNode, tSurf, v, wedge, &
         &            zMNode, &
         &            zTranF, &                             ! modify
         &            fC, fIMuDZ, fPeakS, fSlips, fTStar)   ! output
```

`src/SHELLS_v5.0.f90:687`
```text
     &              names, nodes, &
     &              nPlate, numEl, numNod, omega, oneKm, &
     &              radio, radius, rhoAst, rhoBar, rhoH2O, &
     &              tAdiab, temLim, tLNode, trHMax, tSurf, &
     &              vTimes, whichP, xNode, yNode, zBAsth, &
     &              zMNode, &
     &              contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/SHELLS_v5.0.f90:722`
```text
     &             nCond, nFl, nodCon, nodeF, nodes, numEl, &
     &             oneKm, radio, radius, &
     &             rhoAst, rhoBar, rhoH2O, sigZZI, &
     &             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
     &             xNode, yNode, zMNode, &
     &             fBase)                    ! output

```

`src/SHELLS_v5.0.f90:748`
```text
     &            radius, rhoBar, rhoH2O, sita, slide, &
     &            tauMax, temLim, title1, &
     &            title2, title3, tLInt, tLNode, trHMax, &
     &            tSurf, vBCArg, vBCMag, visMax, &
     &            wedge, zMNode, zMoho, 999, &
     &            v, &                                          ! modify
     &            eRate, eta, fIMuDZ, fPeakS, fSlips, &         ! output
```

`src/SHELLS_v5.0.f90:771`
```text
     &              sigZZI, sita, &
     &              tauMat, tauZZI, tauZZN, temLim, &
     &              title1, title2, title3, tLNode, &
     &              tSurf, v, wedge, xNode, yNode, &
     &              zMNode, &
     &              sigHB, &                              ! modify
     &              comp, &                               ! output
```

`src/ShellSetMain.f90:588`
```text
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
      &          radio , radius,    refStr, rhoAst, rhoBar, &
      &          rhoH2O, TAdiab,    tauMax, temLim, title3, &
      &          trHMax, TSurf,     vTimes, zBAsth, pltRef)
    close(1)

    Run = .True.
```

`src/ShellSetMain.f90:611`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
    if(Verbose) then
      write(iUnitVerb,"(/A)")"The following variables were updated before being used by any of OrbData, Shells or OrbScore"
```

`src/ShellSetMain.f90:775`
```text
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
        end if


```

### `temLim`

`INPUT/iEarth5-049.in:27`
```text
2.7,3.20        conduc = thermal conductivity, crust/mantle (for SI units, in W/m/C)
3.5E-7,3.2E-8   radio = volumetric radioactive heat production (for SI units, in W/m**3)
273.            tSurf = surface temperature of planet, in K
1223.,1673.     temLim = temperature limits (due to melting) in crust/mantle-lithosphere, in Kelvin(!)
50              maxItr = maximum number of iterations of the velocity solution (e.g., 80?)
0.0005          okToQt = acceptable level of fractional change in RMS velocity which stops iteration
50.E6           refStre = reference level of shear stress in lithosphere, for initiating linearization of rheology, in Pa
```

`src/MOD_Data.f90:48`
```text
     &                    geoth5, geoth6, geoth7, geoth8, &         ! INTENT(IN)
     &                     gMean, &                                 ! INTENT(IN)
     &                    iUnitT,  oneKm, rhoAst, rhoBar, rhoH2O, & ! INTENT(IN)
     &                    temLim,     zM,  zStop, &                 ! INTENT(IN)
     &                     tauZZ, sigZZB)                           ! INTENT(OUT)

!   Calculates "tauZZ", the vertical integral through the plate
```

`src/MOD_Data.f90:74`
```text
                           &  gMean
       INTEGER, INTENT(IN) :: iUnitT
       REAL*8, INTENT(IN) :: oneKm, rhoAst, rhoBar, rhoH2O,         &
                           & temLim,    zM,  zStop
       REAL*8, INTENT(OUT) :: tauZZ, sigZZB
!   Argument arrays:
       DIMENSION alphaT(2), rhoBar(2), temLim(2)
```

`src/MOD_Data.f90:77`
```text
                           & temLim,    zM,  zStop
       REAL*8, INTENT(OUT) :: tauZZ, sigZZB
!   Argument arrays:
       DIMENSION alphaT(2), rhoBar(2), temLim(2)

       INTEGER, PARAMETER :: nDRef = 300
       INTEGER :: i, j, lastDR, layer1, layer2, n1, n2, nStep
```

`src/MOD_Data.f90:88`
```text
       REAL*8, DIMENSION(0:nDRef) :: dRef, PRef

!   Statement functions:
       tempC(h) = MIN(temLim(1), geoth1 + geoth2 * h + geoth3 * h**2 &
     &                                       + geoth4 * h**3)
       tempM(h) = MIN(temLim(2), geoth5 + geoth6 * h + geoth7 * h**2 &
     &                                       + geoth8 * h**3)
```

`src/MOD_Data.f90:90`
```text
!   Statement functions:
       tempC(h) = MIN(temLim(1), geoth1 + geoth2 * h + geoth3 * h**2 &
     &                                       + geoth4 * h**3)
       tempM(h) = MIN(temLim(2), geoth5 + geoth6 * h + geoth7 * h**2 &
     &                                       + geoth8 * h**3)

!   Create reference temperature & density profiles to depth of nDRef km:
```

`src/MOD_Data.f90:222`
```text
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                    TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                    elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                    thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                    arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

`src/MOD_Data.f90:268`
```text
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
                           & TAsthK, temLim,  TSurf
       INTEGER, INTENT(IN) ::    nAX,    nAY,    nCX,    nCY,    nEX,    nEY, &
                            & iUnitL, iUnitT, &
                            &    nQX,    nQY,    nSX,    nSY
```

`src/MOD_Data.f90:279`
```text
        !Argument arrays ALLOCATED and dimensioned in calling program:
        DIMENSION aArray(:, :), cArray(:, :), eArray(:, :), qArray(:, :), sArray(:, :)
        !Argument arrays with (crust:mantle) values:
        DIMENSION alphaT(2), conduc(2), radio(2), rhoBar(2), temLim(2)
!---------------------------------------------------------------------
        !Internal variables:
        INTEGER :: ic1, ic2, ir1, ir2
```

`src/MOD_Data.f90:710`
```text
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &               gMean, iUnitT, &                     ! INTENT(IN)
     &               oneKm, rhoAst, rhoBar, rhoH2O, &     ! INTENT(IN)
     &              temLim, thickC, thickC + thickM, &    ! INTENT(IN)
     &               tauZZ, sigZZB)                       ! INTENT(OUT)

!   Trial value of chemical_density_anomaly:
```

`src/MOD_Data.f90:729`
```text
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &              gMean, iUnitT, &                      ! INTENT(IN)
     &              oneKm, rhoAst, rhoBar, rhoH2O, &      ! INTENT(IN)
     &              temLim, thickC, thickC + thickM, &    ! INTENT(IN)
     &              tauZZ, sigZZB)                        ! INTENT(OUT)

!   Test for successful calculation:
```

`src/MOD_SharedVars.f90:45`
```text
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
        & radio, radius, refStr, rhoAst, rhoBar, rhoH2O, &
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
```

`src/MOD_SharedVars.f90:50`
```text

dimension alphaT(2), conduc(2), &
        & aCreep(2), bCreep(2), cCreep(2), dCreep(2), & ! default d_XXXX(1:2) = LR_set_XXXX(1:2, 0)
        & radio(2),  rhoBar(2), tauMax(2), temLim(2), &
		& omega(3, nPlate)

integer :: i,j
```

`src/MOD_ShellSet.f90:164`
```text
  & trim(VarNames(i)) /= 'oneKm' .AND. trim(VarNames(i)) /= 'radius' .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  & trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  & trim(VarNames(i)) /= 'radio_C' .AND. trim(VarNames(i)) /= 'radio_M' .AND. trim(VarNames(i)) /= 'tSurf' .AND. &
  & trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
    Abort = .True.
  end if
```

`src/MOD_ShellSet.f90:236`
```text
  &  trim(VarNames(i)) /= 'oneKm'    .AND. trim(VarNames(i)) /= 'radius'   .AND. trim(VarNames(i)) /= 'alphaT_C' .AND. &
  &  trim(VarNames(i)) /= 'alphaT_M' .AND. trim(VarNames(i)) /= 'conduc_C' .AND. trim(VarNames(i)) /= 'conduc_M' .AND. &
  &  trim(VarNames(i)) /= 'radio_C'  .AND. trim(VarNames(i)) /= 'radio_M'  .AND. trim(VarNames(i)) /= 'tSurf'    .AND. &
  &  trim(VarNames(i)) /= 'temLim_C' .AND. trim(VarNames(i)) /= 'temLim_M') then
    print*,'One or more Variable names not recognised'
    Abort = .True.
  end if
```

`src/MOD_ShellSet.f90:572`
```text
      frmt = trim(frmt)//"X,ES12.5,"
    case('tSurf')
      frmt = trim(frmt)//"X,F11.5,"
    case('temLim_C')
      frmt = trim(frmt)//"X,F11.5,"
    case('temLim_M')
      frmt = trim(frmt)//"X,F11.5,"
```

`src/MOD_ShellSet.f90:574`
```text
      frmt = trim(frmt)//"X,F11.5,"
    case('temLim_C')
      frmt = trim(frmt)//"X,F11.5,"
    case('temLim_M')
      frmt = trim(frmt)//"X,F11.5,"
    case default
      print*,'One or more Variable Names not recognised inside FormatStrings'
```

`src/MOD_ShellSet.f90:1072`
```text
  if(trim(VarNames(i)) == 'radio_C')  OData = .True.
  if(trim(VarNames(i)) == 'radio_M')  OData = .True.
  if(trim(VarNames(i)) == 'tSurf')    OData = .True.
  if(trim(VarNames(i)) == 'temLim_C') OData = .True.
  if(trim(VarNames(i)) == 'temLim_M') OData = .True.
  i = i+1
end do
```

`src/MOD_ShellSet.f90:1073`
```text
  if(trim(VarNames(i)) == 'radio_M')  OData = .True.
  if(trim(VarNames(i)) == 'tSurf')    OData = .True.
  if(trim(VarNames(i)) == 'temLim_C') OData = .True.
  if(trim(VarNames(i)) == 'temLim_M') OData = .True.
  i = i+1
end do

```

`src/MOD_ShellSet.f90:1084`
```text
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
```

`src/MOD_ShellSet.f90:1090`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(:),intent(in) :: VarNames
```

`src/MOD_ShellSet.f90:1170`
```text
      radio(2) = VarValues(i)
    case('tSurf')
      tSurf = VarValues(i)
    case('temLim_C')
      temLim(1) = VarValues(i)
    case('temLim_M')
      temLim(2) = VarValues(i)
```

`src/MOD_ShellSet.f90:1171`
```text
    case('tSurf')
      tSurf = VarValues(i)
    case('temLim_C')
      temLim(1) = VarValues(i)
    case('temLim_M')
      temLim(2) = VarValues(i)
    case default
```

`src/MOD_ShellSet.f90:1172`
```text
      tSurf = VarValues(i)
    case('temLim_C')
      temLim(1) = VarValues(i)
    case('temLim_M')
      temLim(2) = VarValues(i)
    case default
      print*,'One or more Variable Names not recognised inside Variable_Update'
```

`src/MOD_ShellSet.f90:1173`
```text
    case('temLim_C')
      temLim(1) = VarValues(i)
    case('temLim_M')
      temLim(2) = VarValues(i)
    case default
      print*,'One or more Variable Names not recognised inside Variable_Update'
  end select
```

`src/MOD_ShellSet.f90:1186`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
```

`src/MOD_ShellSet.f90:1191`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(1) :: UpName
```

`src/MOD_ShellSet.f90:1220`
```text
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
end do	

```

`src/MOD_ShellSet.f90:2425`
```text
&                    gradie, iConve, iPVRef, &
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
&                    radius, refStr, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, tauMax, temLim, title3, &
&                    trHMax, tSurf,  vTimes, zBAsth, pltRef)


```

`src/MOD_ShellSet.f90:2444`
```text
       REAL*8, INTENT(OUT) :: fFric , gMean , gradie                                          ! output
       INTEGER, INTENT(OUT) :: iConve, iPVRef, maxItr                                         ! output
       REAL*8, INTENT(OUT) :: okDelV, okToQt, oneKm,  radio, radius, refStr, &                ! output
          & rhoAst, rhoBar, rhoH2O, tAdiab, tauMax, temLim                                    ! output
       CHARACTER*100, INTENT(OUT) :: title3                                                    ! output
       REAL*8, INTENT(OUT) :: trHMax, tSurf,  vTimes, zBAsth                                  ! output
     ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

`src/MOD_ShellSet.f90:2453`
```text
       REAL*8 tempV, vector
       DIMENSION aCreep(2), alphaT(2), bCreep(2), cCreep(2), conduc(2), &
     &           dCreep(2), names(numplt), radio(2), &
     &           rhoBar(2), tauMax(2), temLim(2), tempv(2), vector(2)

       IF(Verbose) WRITE(iUnitT,1) iunit7
    1  FORMAT(//' Attempting to read input parameter file from unit ', I3/)
```

`src/MOD_ShellSet.f90:2779`
```text
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             temLim)              ! output
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
```

`src/MOD_ShellSet.f90:2780`
```text

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             temLim)              ! output
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2781`
```text
       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             temLim)              ! output
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: temLim must be positive in each layer."
```

`src/MOD_ShellSet.f90:2783`
```text
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: temLim must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2784`
```text
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: temLim must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_Shells.f90:544`
```text
&                    numEl, numNod, oneKm, oVB, radio, radius, &
&                    rhoAst, rhoBar, rhoH2O, &
&                    sigZZI, sita, &
&                    tauMat, tauZZI, tauZZN, temLim, &
&                    title1, title2, title3, &
&                    tLNode, tSurf, v, wedge, xNode, yNode, zMNode, &
&                    sigHB, &                               ! modify
```

`src/MOD_Shells.f90:599`
```text
LOGICAL, INTENT(IN) :: log_force_balance                                          ! input
REAL*8, INTENT(IN) :: oneKm, oVB, radio, radius, rhoAst, rhoBar, rhoH2O, &        ! input
				   & sigZZI, sita, &                                             ! input
				   & tauMat, tauZZI, tauZZN, temLim                              ! input
CHARACTER*100, INTENT(IN) :: title1, title2, title3                                ! input
REAL*8, INTENT(IN) :: tLNode, tSurf                                               ! input
DOUBLE PRECISION, INTENT(IN) :: v                                                 ! input
```

`src/MOD_Shells.f90:646`
```text
&           outVec(2, 7, mxEl), oVB(2, 7, mxEl), radio(2), rhoBar(2), &
&           sigHB(2, 7, mxEl), sigZZI(7, mxEl), sita(7, mxEl), &
&           tauMat(3, 7, mxEl), tauZZI(7, mxEl), tauZZN(mxNode), &
&           temLim(2), tLNode(mxNode), &
&           v(2, mxNode), &
&           xNode(mxNode), yNode(mxNode), zMNode(mxNode)
DATA cx / '+S' / , cy / '+E' /
```

`src/MOD_Shells.f90:773`
```text
&             nCond, nFl, nodCon, nodeF, nodes, numEl, &
&             oneKm, radio, radius, &
&             rhoAst, rhoBar, rhoH2O, sigZZI, &
&             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&             xNode, yNode, zMNode, &
&             fBase)                   ! output
DO 210 i = 1, nEntry
```

`src/MOD_Shells.f90:897`
```text
&             nCond, nFl, nodCon, nodeF, nodes, numEl, &
&             oneKm, radio, radius, &
&             rhoAst, rhoBar, rhoH2O, sigZZI, &
&             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&             xNode, yNode, zMNode, &
&             fBase)                   ! output
DO 310 i = 1, nEntry
```

`src/MOD_Shells.f90:2260`
```text
&                    geoth4, &
&                    pl0, pw0, &
&                    rhoBar, rhoH2O, sigHBi, &
&                    thick, temLim, &
&                    visMax, zOfTop, &
&                    pT1dE1, pT1dE2, &         ! output
&                    pT2dE1, pT2dE2, &
```

`src/MOD_Shells.f90:2304`
```text
&      geoth1, geoth2, geoth3, geoth4, &                                                  ! input
&      pl0, pw0, &                                                                        ! input
&      rhoBar, rhoH2O, sigHBi, &                                                          ! input
&      thick, temLim, visMax, zOfTop                                                      ! input
REAL*8, INTENT(OUT) :: pT1, pT2, pT1dE1, pT1dE2, pT2dE1, pT2dE2, zTran                  ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
!      Internal variables:
```

`src/MOD_Shells.f90:2493`
```text

	z0 = 0.0D0
	sf0 = dSFdEV * (pl0 - Biot * pw0)
	t0 = MIN(temLim, geoth1)
	argume = (bCreep + cCreep * zOfTop) / t0
!           Avoid overflow in EXP() by limiting the argument:
	argume = MAX(MIN(argume, 87.0D0), -87.0D0)
```

`src/MOD_Shells.f90:2507`
```text
&       0.250D0 * geoth4 * z1**3
	rhoUse = rhoBar * (1.0D0 - alphaT * tMean)
	sf1 = sf0 + dSFdEV * (rhoUse - Biot * rhoH2O) * g * thick
	t1 = MIN(temLim, geoth1 + geoth2 * z1 + geoth3 * z1**2 + geoth4 * z1**3)
	argume = (bCreep + cCreep * (zOfTop + z1)) / t1
	argume = MAX(MIN(argume, 87.0D0), -87.0D0)
	sc1 = 2.0D0 * (visInf * eSCrit) * EXP(argume)
```

`src/MOD_Shells.f90:2536`
```text
			  tMean = 0.50D0 * (t0 + t1)
			  rhoUse = rhoBar * (1.0D0 - alphaT * tMean)
			  sfh = sf0 + dSFdEV * (rhoUse - Biot * rhoH2O) * g * (zh - z0)
			  th = MIN(temLim, geoth1 + geoth2 * zh + geoth3 * zh**2 + &
&                              geoth4 * zh**3)
			  argume = (bCreep + cCreep * (zOfTop + zh)) / th
			  argume = MAX(MIN(argume, 87.0D0), -87.0D0)
```

`src/MOD_Shells.f90:2841`
```text
!               (upper surface of hard crust, or Moho) and
!                may not be absolute depth.
		 t = geoth1 + geoth2 * z + geoth3 * z**2 + geoth4 * z**3
		 t = MIN(t, temLim)
		 argume = (bCreep + cCreep * (zOfTop + z)) / t
!                Prevent over/underflow in EXP() by limiting the argument:
		 argume = MAX(MIN(argume, 87.0D0), -87.0D0)
```

`src/MOD_Shells.f90:3737`
```text
&                    names, nodes, &
&                    nPlate, numEl, numNod, omega, oneKm, &
&                    radio, radius, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, temLim, tLNode, trHMax, tSurf, &
&                    vTimes, whichP, xNode, yNode, zBAsth, &
&                    zMNode, &
&                    contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/MOD_Shells.f90:3762`
```text
CHARACTER*2, INTENT(IN) :: names                                                       ! input
INTEGER, INTENT(IN) :: nodes, nPlate, numEl, numNod                                    ! input
REAL*8, INTENT(IN) :: omega, oneKm, radio, radius, rhoAst, rhoBar, rhoH2O, &           ! input
				   & tAdiab, temLim, tLNode, trHMax, tSurf, vTimes                    ! input
INTEGER, INTENT(IN) :: whichP                                                          ! input
REAL*8, INTENT(IN) :: xNode, yNode                                                     ! input
REAL*8, INTENT(IN) :: zBAsth, zMNode                                                   ! input
```

`src/MOD_Shells.f90:3799`
```text
&           oVB(2, 7, mxEl), &
&           pulled(7, mxEl), radio(2), rhoBar(2), &
&           sigZZI(7, mxEl), tauZZI(7, mxEl), tauZZN(mxNode), &
&           temLim(2), tLNode(mxNode), &
&           tLInt(7, mxEl), whichP(mxNode), &
&           vm(2, mxNode), xNode(mxNode), yNode(mxNode), &
&           zMNode(mxNode), zMoho(7, mxEl)
```

`src/MOD_Shells.f90:3985`
```text
&                   geoth5, geoth6, geoth7, geoth8, &
&                   gMean, &
&                   iUnitT, oneKm, rhoAst, rhoBar, rhoH2O, &
&                   temLim, zMNode(i), zMNode(i) + tLNode(i), &
&                   tauZZN(i), atNode(i))                   ! output
100  CONTINUE
CALL Interp (atNode, mxEl, mxNode, nodes, numEl, & ! input
```

`src/MOD_Shells.f90:4191`
```text
&                   nCond, nFl, nodCon, nodeF, nodes, numEl, &
&                   oneKm, radio, radius, rhoAst, &
&                   rhoBar, rhoH2O, sigZZI, sita, &
&                   tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
&                   xNode, yNode, zMNode, &
&                   fBase)                  ! output

```

`src/MOD_Shells.f90:4211`
```text
INTEGER, INTENT(IN) :: iCond, iUnitT, mxBn, mxDOF, mxEl, mxFEl, mxNode, &              ! input
	 & nCond, nFl, nodCon, nodeF, nodes, numEl                                        ! input
REAL*8, INTENT(IN) :: oneKm, radio, radius, rhoAst, rhoBar, rhoH2O, sigZZI, sita, &    ! input
  & tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, xNode, yNode, zMNode                ! input
DOUBLE PRECISION, INTENT(OUT) :: fBase                                                 ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
DOUBLE PRECISION fPoint, fPhi, fGauss
```

`src/MOD_Shells.f90:4236`
```text
	& x, x0, x1, x2, xout, xta, y, y0, y1, y2, yout, yta, z, zA, zM, zta, zta1, zta2
DOUBLE PRECISION fp1, fp2
DIMENSION alphaT(2), conduc(2), &
&           radio(2),  rhoBar(2), temLim(2)
DIMENSION phi(2), points(3, 7), theta(2), weight(7)
DIMENSION area(mxEl), density_anomaly(mxNode), &
&           detJ(7, mxEl), dQdTdA(mxNode), &
```

`src/MOD_Shells.f90:4523`
```text
&                                                 gMean, iUnitT, &
&                                                 oneKm, rhoAst, &
&                                                 rhoBar, rhoH2O, &
&                                                 temLim, zm, z, &
&                                                 tauzz, sigzzb) ! output
								  tzz = tzz + sigzzb * dz
							 END IF ! atSea, or NOT
```

`src/MOD_Shells.f90:6487`
```text
&                  nodeF, nodes, nUB, numEl, numNod, offMax, &
&                  offset, okToQt, oneKm, oVB, pulled, &
&                  radio, radius, rhoBar, rhoH2O, sita, slide, &
&                  tauMax, temLim, title1, &
&                  title2, title3, tLInt, tLNode, trHMax, &
&                  tSurf, vBCArg, vBCMag, visMax, wedge, &
&                  zMNode, zMoho, lastPm, &
```

`src/MOD_Shells.f90:6523`
```text
REAL*8, INTENT(IN) :: offMax, offset, okToQt, oneKm, oVB                                ! input
LOGICAL, INTENT(IN) :: pulled                                                           ! input
REAL*8, INTENT(IN) :: radio, radius, rhoBar, rhoH2O, sita, slide                        ! input
REAL*8, INTENT(IN) :: tauMax, temLim                                                    ! input
CHARACTER*100, INTENT(IN) :: title1, title2, title3                                      ! input
REAL*8, INTENT(IN) :: tLInt, tLNode, trHMax, tSurf, vBCArg, vBCMag, visMax, wedge, &    ! input
				   & zMNode, zMoho                                                     ! input
```

`src/MOD_Shells.f90:6582`
```text
&           zMNode(mxNode), zMoho(7, mxEl), &
&           zTranC(2, 7, mxEl), zTranF(2, mxFEl)
DIMENSION alphaT(2), conduc(2), &
&           radio(2),  rhoBar(2), temLim(2)

IF (lastPm /= 999) THEN
  write(ErrorMsg,'(A)') "WRONG NUMBER OF ARGUMENTS IN CALL TO -Pure-!"
```

`src/MOD_Shells.f90:6613`
```text
&              LRn, LR_set_cFric, LR_set_Biot, &
&              LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep, &
&              mxEl, numEl, rhoBar, rhoH2O, &
&              sigHB, tauMat, temLim, tLInt, &
&              visMax, zMoho, &
&              alpha, scoreC, scoreD, tOfset, zTranC) ! output

```

`src/MOD_Shells.f90:6690`
```text
&                   LRn, LR_set_cFric, LR_set_Biot, &
&                   LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep, &
&                   mxEl, numEl, rhoBar, rhoH2O, &
&                   sigHB, tauMat, temLim, tLInt, &
&                   visMax, zMoho, &
&                   alpha, scoreC, scoreD, tOfset, zTranC) ! output
	CALL Mohr (alphaT, conduc, constr, &                     ! input
```

`src/MOD_Shells.f90:9058`
```text
&                    geoth5, geoth6, geoth7, geoth8, &
&                    gMean, &
&                    iUnitT, oneKm, rhoAst, rhoBar, rhoH2O, &
&                    temLim, zM, zStop, &
&                    tauzz, sigzzb)                           ! output

!   Calculates tauzz, the vertical integral through the plate
```

`src/MOD_Shells.f90:9089`
```text
REAL*8, INTENT(IN) :: alphaT, density_anomaly_kgpm3, elevat, geoth1, geoth2, geoth3, & ! input
  & geoth4, geoth5, geoth6, geoth7, geoth8, gMean                                     ! input
INTEGER, INTENT(IN) :: iUnitT                                                          ! input
REAL*8, INTENT(IN) :: oneKm, rhoAst, rhoBar, rhoH2O, temLim, zM, zStop                 ! input
REAL*8, INTENT(OUT) :: tauzz, sigzzb                                                   ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8 TempC, TempM, h ! statement functions
```

`src/MOD_Shells.f90:9102`
```text
!   Internal arrays:
DIMENSION dRef(ndRef), pRef(0:ndRef)
!   Argument arrays:
DIMENSION alphaT(2), rhoBar(2), temLim(2)


!   Statement functions:
```

`src/MOD_Shells.f90:9106`
```text


!   Statement functions:
TempC(h) = MIN(temLim(1), geoth1 + geoth2 * h + geoth3 * h**2 + geoth4 * h**3)
TempM(h) = MIN(temLim(2), geoth5 + geoth6 * h + geoth7 * h**2 + geoth8 * h**3)

!   Create reference temperature & density profiles to depth of ndRef kilometers:
```

`src/MOD_Shells.f90:9107`
```text

!   Statement functions:
TempC(h) = MIN(temLim(1), geoth1 + geoth2 * h + geoth3 * h**2 + geoth4 * h**3)
TempM(h) = MIN(temLim(2), geoth5 + geoth6 * h + geoth7 * h**2 + geoth8 * h**3)

!   Create reference temperature & density profiles to depth of ndRef kilometers:

```

`src/MOD_Shells.f90:9844`
```text
&                    LRn, LR_set_cFric, LR_set_Biot, &
&                    LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep, &
&                    mxEl, numEl, rhoBar, rhoH2O, &
&                    sigHB, tauMat, temLim, tLInt, &
&                    visMax, zMoho, &
&                    alpha, scoreC, scoreD, tOfset, zTranC) ! output

```

`src/MOD_Shells.f90:9882`
```text
REAL*8, INTENT(IN) :: LR_set_cFric, LR_set_Biot, &                                        ! input
				   & LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_dCreep, LR_set_eCreep ! input
INTEGER, INTENT(IN) :: mxEl, numEl                                                        ! input
REAL*8, INTENT(IN) :: rhoBar, rhoH2O, sigHB, tauMat, temLim, tLInt, visMax, zMoho         ! input
REAL*8, INTENT(OUT) :: alpha, scoreC, scoreD, tOfset, zTranC                              ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
INTEGER i, m
```

`src/MOD_Shells.f90:9913`
```text
&           LR_set_cFric(0:LRn), LR_set_Biot(0:LRn), &
&           LR_set_aCreep(1:2, 0:LRn), LR_set_bCreep(1:2, 0:LRn), LR_set_cCreep(1:2, 0:LRn), LR_set_dCreep(1:2, 0:LRn), LR_set_eCreep(0:LRn), &
&           rhoBar(2), sigHB(2, 7, mxEl), &
&           tauMat(3, 7, mxEl), temLim(2), &
&           tLInt(7, mxEl), tOfset(3, 7, mxEl), &
&           zMoho(7, mxEl), zTranC(2, 7, mxEl)
!      Internal variables:
```

`src/MOD_Shells.f90:10016`
```text
&                                  geothC(4, m, i), &
&                                  pl0, pw0, &
&                                  rho_use, rhoH2O, sigHBi, &
&                                  thickC, temLim(1), &
&                                  visMax, zOfTop, &
&                                  pT1dE1, pT1dE2, &      ! output
&                                  pT2dE1, pT2dE2, &
```

`src/MOD_Shells.f90:10060`
```text
&                                  geothM(4, m, i), &
&                                  pl0, pw0, &
&                                  rho_use, rhoH2O, sigHBi, &
&                                  thickM, temLim(2), &
&                                  visMax, zOfTop, &
&                                  pT1dE1, pT1dE2, &       ! output
&                                  pT2dE1, pT2dE2, &
```

`src/OrbData5.f90:539`
```text
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                   TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                   elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                   thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                   arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

`src/SHELLS_v5.0.f90:687`
```text
     &              names, nodes, &
     &              nPlate, numEl, numNod, omega, oneKm, &
     &              radio, radius, rhoAst, rhoBar, rhoH2O, &
     &              tAdiab, temLim, tLNode, trHMax, tSurf, &
     &              vTimes, whichP, xNode, yNode, zBAsth, &
     &              zMNode, &
     &              contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/SHELLS_v5.0.f90:722`
```text
     &             nCond, nFl, nodCon, nodeF, nodes, numEl, &
     &             oneKm, radio, radius, &
     &             rhoAst, rhoBar, rhoH2O, sigZZI, &
     &             sita, tauZZI, tauZZN, temLim, tLNode, tSurf, wedge, &
     &             xNode, yNode, zMNode, &
     &             fBase)                    ! output

```

`src/SHELLS_v5.0.f90:746`
```text
     &            nodeF, nodes, nUB, numEl, numNod, offMax, &
     &            offset, okToQt, oneKm, oVB, pulled, radio, &
     &            radius, rhoBar, rhoH2O, sita, slide, &
     &            tauMax, temLim, title1, &
     &            title2, title3, tLInt, tLNode, trHMax, &
     &            tSurf, vBCArg, vBCMag, visMax, &
     &            wedge, zMNode, zMoho, 999, &
```

`src/SHELLS_v5.0.f90:769`
```text
     &              numEl, numNod, oneKm, oVB, radio, radius, &
     &              rhoAst, rhoBar, rhoH2O, &
     &              sigZZI, sita, &
     &              tauMat, tauZZI, tauZZN, temLim, &
     &              title1, title2, title3, tLNode, &
     &              tSurf, v, wedge, xNode, yNode, &
     &              zMNode, &
```

`src/ShellSetMain.f90:587`
```text
      &          everyP, fFric,     gMean , gradie, iConve, &
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
      &          radio , radius,    refStr, rhoAst, rhoBar, &
      &          rhoH2O, TAdiab,    tauMax, temLim, title3, &
      &          trHMax, TSurf,     vTimes, zBAsth, pltRef)
    close(1)

```

`src/ShellSetMain.f90:611`
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
    if(Verbose) then
      write(iUnitVerb,"(/A)")"The following variables were updated before being used by any of OrbData, Shells or OrbScore"
```

`src/ShellSetMain.f90:775`
```text
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
        end if


```

### `TAsthK`

`src/MOD_Data.f90:222`
```text
     &                    qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                     radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                    sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                    TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                    elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                    thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                    arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

`src/MOD_Data.f90:268`
```text
                           & qArray,    qX1,    qDX,    qX2,    qDY,    qY2, &
                           &  radio, rhoAst, rhoBar, rhoH2O, &
                           & sArray,    sX1,    sDX,    sX2,    sDY,    sY2, &
                           & TAsthK, temLim,  TSurf
       INTEGER, INTENT(IN) ::    nAX,    nAY,    nCX,    nCY,    nEX,    nEY, &
                            & iUnitL, iUnitT, &
                            &    nQX,    nQY,    nSX,    nSY
```

`src/MOD_Data.f90:522`
```text
            q_gdh1 = MAX(q_gdh1, qLimit)
            q_gdh1 = MIN(q_gdh1, qLim1)
            q_radioactivity = 0.007D0
            delta_T = TAsthK - TSurf
            h_Earth3 = (delta_T * conduc(2)) / (q_gdh1 - q_radioactivity)

!        (3)Take geometric mean of this "Earth3" or "old OrbData"
```

`src/MOD_Data.f90:626`
```text
!      margins, where CRUST2 shows thick crust!

       test = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       IF (test > TAsthK) THEN
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
```

`src/MOD_Data.f90:627`
```text

       test = geoth1 + geoth2 * thickC + geoth3 * thickC**2
       IF (test > TAsthK) THEN
            TErr0r = test - TAsthK
            deltaQ = -TErr0r * conduc(1) / thickC
            heatFl = heatFl + deltaQ
            qLimit = qLim0 + dQL_dE * elevat
```

`src/MOD_Data.f90:634`
```text
            heatFl = MAX(heatFl, qLimit)
            heatFl = MIN(heatFl, qLim1)
            geoth2 = heatFl / conduc(1)
            TMoho = TAsthK
            geoth5 = TMoho
            qRed = heatFl - thickC * radio(1)
            geoth6 = qRed / conduc(2)
```

`src/MOD_Data.f90:644`
```text
!     (referring to GEOTHerm without this effect):

       test = geoth5 + geoth6 * thickM + geoth7 * thickM**2
       TErr0r = test - TAsthK
       total_lithosphere = thickC + thickM
       delta_quadratic = -TErr0r / total_lithosphere**2
       cooling_curvature = -2.0D0 * delta_quadratic
```

`src/MOD_Data.f90:678`
```text
!                   Bird's notes of 2005.06.15.

                 z_star = (geoth7 * thickC**2 + geoth5 - &
     &                     geoth6 * thickC - TAsthK) / &
     &                    (geoth7 * thickC - 0.5D0 * geoth6)
                 m_star = z_star - thickC
                 thickM = MAX(MIN(m_star, thickM), 0.0D0)
```

`src/MOD_Data.f90:683`
```text
                 m_star = z_star - thickC
                 thickM = MAX(MIN(m_star, thickM), 0.0D0)
                 total_lithosphere = thickC + thickM
                 TErr0r = (geoth5 + geoth6 * thickM + geoth7 * thickM**2) - TAsthK
                 delta_quadratic = -TErr0r / total_lithosphere**2
                 cooling_curvature = -2.0D0 * delta_quadratic
            END IF
```

`src/MOD_Data.f90:739`
```text

!   Geotherm might not connect to asthenosphere adiabat:
       test = geoth5 + geoth6 * thickM + geoth7 * thickM**2
       TErr0r = test - TAsthK
       badT = (ABS(TErr0r) > 20.0D0) ! 20 degrees Kelvin

       IF (badP) THEN
```

`src/MOD_Shells.f90:3781`
```text
INTEGER i, iconv2, m
REAL*8 baseT, delta_quadratic, difMag, dTdZC, dTdZM, &
	& geoth1, geoth2, geoth3, geoth4, geoth5, geoth6, geoth7, geoth8, &
	& huge, q, shrMag, tAsthK, test, terr0r, vtime2, z
DIMENSION alphaT(2), atNode(mxNode), &
&           basal(2, mxNode),  &
&           conduc(2), contin(7, mxEl), &
```

`src/MOD_Shells.f90:3898`
```text
!                spreading ridge.
!                The correct way is to set curviness(m, i) to make the
!                geotherm of each integration point arrive at
!                temperature tAsthK = tAdiab + gradie * 100.D3
!                at depth (in lithosphere) of
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------
```

`src/MOD_Shells.f90:3903`
```text
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------

tAsthK = tAdiab + gradie * 100.0D3

geoth1 = tSurf
geoth3 = -0.5D0 * radio(1) / conduc(1)
```

`src/MOD_Shells.f90:3935`
```text
		 geothM(3, m, i) = geoth7
		 geothM(4, m, i) = geoth8

!            Now, correct geotherm to hit tAsthK:

		 IF (tLInt(m, i) > 0.0D0) THEN
			  test = geothM(1, m, i) + &
```

`src/MOD_Shells.f90:3948`
```text
&                       geothC(3, m, i) * zMoho(m, i)**2 + &
&                       geothC(4, m, i) * zMoho(m, i)**3
		 END IF
		 terr0r = test - tAsthK
		 delta_quadratic = -terr0r / (zMoho(m, i) + tLInt(m, i))**2
		 curviness(m, i) = -2.0D0 * delta_quadratic
		 geothC(3, m, i) = geoth3 + delta_quadratic
```

`src/OrbData5.f90:45`
```text
integer :: nCX,nCY,nSX,nSY,iNode
integer :: nDomainX,nDomainY,nLithoX,nLithoY,domainClass,domainRow,domainCol
integer :: lithoRow,lithoRow2,lithoCol,lithoCol2
real*8 :: TAsthK,dQdTdA,elev,fDip
real*8 :: offset,xNode,yNode,area,detJ,dXs,dYs,dXSP,dYSP,fLen,fpflt,fpsfer,fArg,sita
real*8 :: eX1,eX2,eDX,eY1,eY2,eDY
real*8 :: qX1,qX2,qDX,qY1,qY2,qDY,qLimit,aX1,aX2,aDX,aY1,aY2,aDY
```

`src/OrbData5.f90:294`
```text
!      from the asthenosphere adiabat in the parameter file,
!      evaluated at (rather arbitrarily) 100 km depth:

       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

!   Read finite-element grid on unit 2:

```

`src/OrbData5.f90:539`
```text
     &                   qArray,    qX1,    qDX,    qX2,    nQX,    qDY,    qY2,    nQY, & ! INTENT(IN)
     &                    radio, rhoAst, rhoBar, rhoH2O, &                                 ! INTENT(IN)
     &                   sArray,    sX1,    sDX,    sX2,    nSX,    sDY,    sY2,    nSY, & ! INTENT(IN)
     &                   TAsthK, temLim,  TSurf, &                                         ! INTENT(IN)
     &                   elevat, heatFl, &                                                 ! INTENT(INOUT)
     &                   thickC, thickM, chemical_delta_rho, cooling_curvature, &          ! INTENT(OUT)
     &                   arcanaMode,arcanaOcean,requestedTotalLithosphere, &
```

### `TADIAB`

`INPUT/iEarth5-049.in:11`
```text
0.,0.0171       cCreep = derivative of exponential numerator w.r.t. depth, in K/m, crust/mantle
5.E8,5.E8       dCreep = maximum shear stress at any temperature/strain-rate, Pa, crust/mantle
0.333333        eCreep = exponent on strain-rate in creep-strength law, = 1/n, same for crust & mantle
1412.,6.1E-4    tAdiab, gradie = intercept (in K) and slope (in K/m) of upper mantle adiabat
400.E3          zBAsth = depth (in m) of base of upper mantle (end of olivine=rich layer)
AF              pltRef = plate held fixed in boundary conditions (or reference frame in global model)
0,1.00 	        iConve, vTimes = convection under lithosphere (codes 0:6 given below, vTimes needed for iConve > 0; also see trHMax below)
```

`src/MOD_SharedVars.f90:45`
```text
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
        & radio, radius, refStr, rhoAst, rhoBar, rhoH2O, &
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
```

`src/MOD_ShellSet.f90:156`
```text
  &  trim(VarNames(i)) /= 'Byerly' .AND. trim(VarNames(i)) /= 'aCreep_C' .AND. trim(VarNames(i)) /= 'aCreep_M' .AND. &
  & trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  & trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  & trim(VarNames(i)) /= 'eCreep' .AND. trim(VarNames(i)) /= 'tAdiab' .AND. trim(VarNames(i)) /= 'gradie' .AND. &
  & trim(VarNames(i)) /= 'zBAsth' .AND. trim(VarNames(i)) /= 'pltRef' .AND. trim(VarNames(i)) /= 'iConve' .AND. &
  & trim(VarNames(i)) /= 'trHMax' .AND. trim(VarNames(i)) /= 'tauMax' .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
```

`src/MOD_ShellSet.f90:228`
```text
  &  trim(VarNames(i)) /= 'Byerly'   .AND. trim(VarNames(i)) /= 'aCreep_C' .AND. trim(VarNames(i)) /= 'aCreep_M' .AND. &
  &  trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  &  trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  &  trim(VarNames(i)) /= 'eCreep'   .AND. trim(VarNames(i)) /= 'tAdiab'   .AND. trim(VarNames(i)) /= 'gradie'   .AND. &
  &  trim(VarNames(i)) /= 'zBAsth'   .AND. trim(VarNames(i)) /= 'pltRef'   .AND. trim(VarNames(i)) /= 'iConve'   .AND. &
  &  trim(VarNames(i)) /= 'trHMax'   .AND. trim(VarNames(i)) /= 'tauMax'   .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
```

`src/MOD_ShellSet.f90:530`
```text
      frmt = trim(frmt)//"X,ES12.5,"
    case('eCreep')
      frmt = trim(frmt)//"X,F12.6,"
    case('tAdiab')
      frmt = trim(frmt)//"X,F12.6,"
    case('gradie')
      frmt = trim(frmt)//"X,ES12.5,"
```

`src/MOD_ShellSet.f90:1057`
```text
OData = .False.

do while(.not. OData .and. i <= size(VarNames))
  if(trim(VarNames(i)) == 'tAdiab')   OData = .True.
  if(trim(VarNames(i)) == 'gradie')   OData = .True.
  if(trim(VarNames(i)) == 'zBAsth')   OData = .True.
  if(trim(VarNames(i)) == 'trHMax')   OData = .True.
```

`src/MOD_ShellSet.f90:1081`
```text


subroutine Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, & ! Update variable values with user input values
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
```

`src/MOD_ShellSet.f90:1089`
```text

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

```

`src/MOD_ShellSet.f90:1127`
```text
      dCreep(2) = VarValues(i)
    case('eCreep')
      eCreep = VarValues(i)
    case('tAdiab')
      tAdiab = VarValues(i)
    case('gradie')
      gradie = VarValues(i)
```

`src/MOD_ShellSet.f90:1128`
```text
    case('eCreep')
      eCreep = VarValues(i)
    case('tAdiab')
      tAdiab = VarValues(i)
    case('gradie')
      gradie = VarValues(i)
    case('zBAsth')
```

`src/MOD_ShellSet.f90:1183`
```text


subroutine IterVar(fFric, cFric,  Biot,   Byerly, aCreep, & ! Update variable values between 1st & 2nd Shells call
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)
```

`src/MOD_ShellSet.f90:1190`
```text

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

```

`src/MOD_ShellSet.f90:1217`
```text
  if(Verbose) write(iUnitVerb,"(3A)") "Updating ",trim(UpName(1))," with new value from UpVar.in."
  
  call Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, &
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
```

`src/MOD_ShellSet.f90:2425`
```text
&                    gradie, iConve, iPVRef, &
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
&                    radius, refStr, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, tauMax, temLim, title3, &
&                    trHMax, tSurf,  vTimes, zBAsth, pltRef)


```

`src/MOD_ShellSet.f90:2444`
```text
       REAL*8, INTENT(OUT) :: fFric , gMean , gradie                                          ! output
       INTEGER, INTENT(OUT) :: iConve, iPVRef, maxItr                                         ! output
       REAL*8, INTENT(OUT) :: okDelV, okToQt, oneKm,  radio, radius, refStr, &                ! output
          & rhoAst, rhoBar, rhoH2O, tAdiab, tauMax, temLim                                    ! output
       CHARACTER*100, INTENT(OUT) :: title3                                                    ! output
       REAL*8, INTENT(OUT) :: trHMax, tSurf,  vTimes, zBAsth                                  ! output
     ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

`src/MOD_ShellSet.f90:2584`
```text
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
```

`src/MOD_ShellSet.f90:2585`
```text
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2586`
```text

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
```

`src/MOD_ShellSet.f90:2588`
```text
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_Shells.f90:3737`
```text
&                    names, nodes, &
&                    nPlate, numEl, numNod, omega, oneKm, &
&                    radio, radius, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, temLim, tLNode, trHMax, tSurf, &
&                    vTimes, whichP, xNode, yNode, zBAsth, &
&                    zMNode, &
&                    contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/MOD_Shells.f90:3762`
```text
CHARACTER*2, INTENT(IN) :: names                                                       ! input
INTEGER, INTENT(IN) :: nodes, nPlate, numEl, numNod                                    ! input
REAL*8, INTENT(IN) :: omega, oneKm, radio, radius, rhoAst, rhoBar, rhoH2O, &           ! input
				   & tAdiab, temLim, tLNode, trHMax, tSurf, vTimes                    ! input
INTEGER, INTENT(IN) :: whichP                                                          ! input
REAL*8, INTENT(IN) :: xNode, yNode                                                     ! input
REAL*8, INTENT(IN) :: zBAsth, zMNode                                                   ! input
```

`src/MOD_Shells.f90:3898`
```text
!                spreading ridge.
!                The correct way is to set curviness(m, i) to make the
!                geotherm of each integration point arrive at
!                temperature tAsthK = tAdiab + gradie * 100.D3
!                at depth (in lithosphere) of
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------
```

`src/MOD_Shells.f90:3903`
```text
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------

tAsthK = tAdiab + gradie * 100.0D3

geoth1 = tSurf
geoth3 = -0.5D0 * radio(1) / conduc(1)
```

`src/MOD_Shells.f90:3998`
```text
CALL OneBar (continuum_LRi, &                                                   ! input
&              geothC, geothM, gradie, &                                          ! input
&              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&              mxEl, numEl, oneKm, tAdiab, &                                      ! input
&              zBAsth, zMoho, &                                                   ! input
&              glue)                                                              ! output

```

`src/MOD_Shells.f90:6232`
```text
SUBROUTINE OneBar (continuum_LRi, &                                                   ! input
&                    geothC, geothM, gradie, &                                          ! input
&                    LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&                    mxEl, numEl, oneKm, tAdiab, &                                      ! input
&                    zBAsth, zMoho, &                                                   ! input
&                    glue)                                                              ! output

```

`src/MOD_Shells.f90:6246`
```text
INTEGER, INTENT(IN) :: LRn                                                             ! input
REAL*8, INTENT(IN) :: LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep       ! input
INTEGER, INTENT(IN) :: mxEl, numEl                                                     ! input
REAL*8, INTENT(IN) :: oneKm, tAdiab, zBAsth, zMoho                                     ! input
REAL*8, INTENT(OUT) :: glue                                                            ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
INTEGER i, layer, level, limit, m
```

`src/MOD_Shells.f90:6301`
```text
&                   + gt(2) * z &
&                   + gt(3) * z * z &
&                   + gt(4) * z * z * z
			  ta = tAdiab + z * gradie
			  t = MIN(tg, ta)
			  t = MAX(t, 200.0D0)
			  bi = (t_bCreep(layer) + t_cCreep(layer) * z) * ecini
```

`src/OrbData5.f90:294`
```text
!      from the asthenosphere adiabat in the parameter file,
!      evaluated at (rather arbitrarily) 100 km depth:

       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

!   Read finite-element grid on unit 2:

```

`src/SHELLS_v5.0.f90:687`
```text
     &              names, nodes, &
     &              nPlate, numEl, numNod, omega, oneKm, &
     &              radio, radius, rhoAst, rhoBar, rhoH2O, &
     &              tAdiab, temLim, tLNode, trHMax, tSurf, &
     &              vTimes, whichP, xNode, yNode, zBAsth, &
     &              zMNode, &
     &              contin, curviness, delta_rho, geothC, geothM, glue, & ! output
```

`src/ShellSetMain.f90:587`
```text
      &          everyP, fFric,     gMean , gradie, iConve, &
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
      &          radio , radius,    refStr, rhoAst, rhoBar, &
      &          rhoH2O, TAdiab,    tauMax, temLim, title3, &
      &          trHMax, TSurf,     vTimes, zBAsth, pltRef)
    close(1)

```

`src/ShellSetMain.f90:608`
```text
    end if

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
```

`src/ShellSetMain.f90:772`
```text
        if(rpeat==1 .and. FileExist('INPUT/UpVar.in')) then
          if(ThID==1 .and. Verbose) write(iUnitVerb,'(A)') 'UpVar.in file detected, updating listed variables'
          call IterVar(fFric, cFric,  Biot,   Byerly, aCreep, &
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
```

### `GRADIE`

`INPUT/iEarth5-049.in:11`
```text
0.,0.0171       cCreep = derivative of exponential numerator w.r.t. depth, in K/m, crust/mantle
5.E8,5.E8       dCreep = maximum shear stress at any temperature/strain-rate, Pa, crust/mantle
0.333333        eCreep = exponent on strain-rate in creep-strength law, = 1/n, same for crust & mantle
1412.,6.1E-4    tAdiab, gradie = intercept (in K) and slope (in K/m) of upper mantle adiabat
400.E3          zBAsth = depth (in m) of base of upper mantle (end of olivine=rich layer)
AF              pltRef = plate held fixed in boundary conditions (or reference frame in global model)
0,1.00 	        iConve, vTimes = convection under lithosphere (codes 0:6 given below, vTimes needed for iConve > 0; also see trHMax below)
```

`src/MOD_Data.f90:251`
```text
!   thickness is more than ~twice that expected based on heat-flow
!  (and a steady-state assumption), then the lithosphere thickness
!   returned will be limited so as to prevent geotherm overshoot
!   and negative temperature gradients.

!   Algorithm revision by Peter Bird, UCLA, June 2005;
!   syntax revision to Fortran 90 by Peter Bird, UCLA, December 2018.
```

`src/MOD_Data.f90:285`
```text
        INTEGER :: ic1, ic2, ir1, ir2
        LOGICAL :: badP, badT, outsid, needE, needQ, &
      &            warnC1, warnC2, warnM1, warnL2, wayOut
        REAL*8  :: ageMa, bot, c0_of_mantle_gradient, c1_of_mantle_gradient, &
                 & deltaQ, delta_quadratic, delta_T, delta_tS, fc, fr, &
                 & geoth1, geoth2, geoth3, geoth4, geoth5, geoth6, geoth7, geoth8, &
                 & h_Earth3, h_Earth5, h_plate, m_star, &
```

`src/MOD_Data.f90:667`
```text
            t_geoth7 = delta_quadratic - radio(2) / (2.0D0 * conduc(2))

!           Check for temperature maximum within mantle lithosphere:
            c0_of_mantle_gradient = t_geoth6
            c1_of_mantle_gradient = 2. * t_geoth7
            z_of_maximum = c0_of_mantle_gradient / (-c1_of_mantle_gradient)
            IF ((z_of_maximum < thickM) .AND. (z_of_maximum > 0.0D0)) THEN
```

`src/MOD_Data.f90:668`
```text

!           Check for temperature maximum within mantle lithosphere:
            c0_of_mantle_gradient = t_geoth6
            c1_of_mantle_gradient = 2. * t_geoth7
            z_of_maximum = c0_of_mantle_gradient / (-c1_of_mantle_gradient)
            IF ((z_of_maximum < thickM) .AND. (z_of_maximum > 0.0D0)) THEN

```

`src/MOD_Data.f90:669`
```text
!           Check for temperature maximum within mantle lithosphere:
            c0_of_mantle_gradient = t_geoth6
            c1_of_mantle_gradient = 2. * t_geoth7
            z_of_maximum = c0_of_mantle_gradient / (-c1_of_mantle_gradient)
            IF ((z_of_maximum < thickM) .AND. (z_of_maximum > 0.0D0)) THEN

!                Must take corrective action; reduce thickM
```

`src/MOD_Score.f90:1967`
```text
!                    *(1. - Byerly * offset(i) / offMax).
!    This may also be a pore pressure effect, because Byerlee's model is
!    that gouge layers have thickness in proportion to offset, and
!    that they support non-Darcy static pore pressure gradients which
!    allow elevated pore pressures in the core of the gouge, which
!    reduce the effective friction of the fault.

```

`src/MOD_Score.f90:2085`
```text
     &                       (0.50D0 * zTranF(1, i)**2 + zTranF(2, i) * zman + &
     &                        0.50D0 * zTranF(2, i)**2)
                 END IF
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
```

`src/MOD_Score.f90:2510`
```text
!                    *(1. - Byerly * offset(i) / offMax).
!    This may also be a pore pressure effect, because Byerlee's model is
!    that gouge layers have thickness in proportion to offset, and
!    that they support non-Darcy static pore pressure gradients which
!    allow elevated pore pressures in the core of the gouge, which
!    reduce the effective friction of the fault.

```

`src/MOD_Score.f90:2652`
```text
     &                       (0.50D0 * zTranF(1, i)**2 + zTranF(2, i) * zman + &
     &                        0.50D0 * zTranF(2, i)**2)
                 END IF
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
                 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
```

`src/MOD_SharedVars.f90:42`
```text

real*8 :: alphaT, conduc, constr, &
        & fFric, cFric, Biot, Byerly, aCreep, bCreep, cCreep, dCreep, eCreep, & ! default d_XXXX = LR_set_XXXX(0)
        & dipMax, etaMax, fMuMax, gMean, gradie, &
        & offMax, okDelV, okToQt, omega, oneKm, &
        & radio, radius, refStr, rhoAst, rhoBar, rhoH2O, &
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
```

`src/MOD_ShellSet.f90:156`
```text
  &  trim(VarNames(i)) /= 'Byerly' .AND. trim(VarNames(i)) /= 'aCreep_C' .AND. trim(VarNames(i)) /= 'aCreep_M' .AND. &
  & trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  & trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  & trim(VarNames(i)) /= 'eCreep' .AND. trim(VarNames(i)) /= 'tAdiab' .AND. trim(VarNames(i)) /= 'gradie' .AND. &
  & trim(VarNames(i)) /= 'zBAsth' .AND. trim(VarNames(i)) /= 'pltRef' .AND. trim(VarNames(i)) /= 'iConve' .AND. &
  & trim(VarNames(i)) /= 'trHMax' .AND. trim(VarNames(i)) /= 'tauMax' .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
```

`src/MOD_ShellSet.f90:228`
```text
  &  trim(VarNames(i)) /= 'Byerly'   .AND. trim(VarNames(i)) /= 'aCreep_C' .AND. trim(VarNames(i)) /= 'aCreep_M' .AND. &
  &  trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  &  trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  &  trim(VarNames(i)) /= 'eCreep'   .AND. trim(VarNames(i)) /= 'tAdiab'   .AND. trim(VarNames(i)) /= 'gradie'   .AND. &
  &  trim(VarNames(i)) /= 'zBAsth'   .AND. trim(VarNames(i)) /= 'pltRef'   .AND. trim(VarNames(i)) /= 'iConve'   .AND. &
  &  trim(VarNames(i)) /= 'trHMax'   .AND. trim(VarNames(i)) /= 'tauMax'   .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
```

`src/MOD_ShellSet.f90:532`
```text
      frmt = trim(frmt)//"X,F12.6,"
    case('tAdiab')
      frmt = trim(frmt)//"X,F12.6,"
    case('gradie')
      frmt = trim(frmt)//"X,ES12.5,"
    case('zBAsth')
      frmt = trim(frmt)//"X,ES12.5,"
```

`src/MOD_ShellSet.f90:1058`
```text

do while(.not. OData .and. i <= size(VarNames))
  if(trim(VarNames(i)) == 'tAdiab')   OData = .True.
  if(trim(VarNames(i)) == 'gradie')   OData = .True.
  if(trim(VarNames(i)) == 'zBAsth')   OData = .True.
  if(trim(VarNames(i)) == 'trHMax')   OData = .True.
  if(trim(VarNames(i)) == 'rhoH2O')   OData = .True.
```

`src/MOD_ShellSet.f90:1082`
```text

subroutine Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, & ! Update variable values with user input values
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)
```

`src/MOD_ShellSet.f90:1088`
```text
                        &  VarNames,VarValues)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)
```

`src/MOD_ShellSet.f90:1129`
```text
      eCreep = VarValues(i)
    case('tAdiab')
      tAdiab = VarValues(i)
    case('gradie')
      gradie = VarValues(i)
    case('zBAsth')
      zBAsth = VarValues(i)
```

`src/MOD_ShellSet.f90:1130`
```text
    case('tAdiab')
      tAdiab = VarValues(i)
    case('gradie')
      gradie = VarValues(i)
    case('zBAsth')
      zBAsth = VarValues(i)
    case('trHMax')
```

`src/MOD_ShellSet.f90:1184`
```text

subroutine IterVar(fFric, cFric,  Biot,   Byerly, aCreep, & ! Update variable values between 1st & 2nd Shells call
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

```

`src/MOD_ShellSet.f90:1189`
```text
      &                  alphaT, conduc, radio,  tSurf,  temLim)

real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)
```

`src/MOD_ShellSet.f90:1218`
```text
  
  call Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, &
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
```

`src/MOD_ShellSet.f90:2422`
```text
&                    aCreep, alphaT, bCreep, Biot  , &         ! output
&                    Byerly, cCreep, cFric , conduc, &
&                    dCreep, eCreep, everyP, fFric , gMean , &
&                    gradie, iConve, iPVRef, &
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
&                    radius, refStr, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, tauMax, temLim, title3, &
```

`src/MOD_ShellSet.f90:2441`
```text
       REAL*8, INTENT(OUT) :: aCreep, alphaT, bCreep, Biot, Byerly, cCreep, cFric , conduc, & ! output
          & dCreep, eCreep                                                                    ! output
       LOGICAL, INTENT(OUT) :: everyP                                                         ! output
       REAL*8, INTENT(OUT) :: fFric , gMean , gradie                                          ! output
       INTEGER, INTENT(OUT) :: iConve, iPVRef, maxItr                                         ! output
       REAL*8, INTENT(OUT) :: okDelV, okToQt, oneKm,  radio, radius, refStr, &                ! output
          & rhoAst, rhoBar, rhoH2O, tAdiab, tauMax, temLim                                    ! output
```

`src/MOD_ShellSet.f90:2584`
```text
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
```

`src/MOD_ShellSet.f90:2585`
```text
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2586`
```text

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
```

`src/MOD_ShellSet.f90:2588`
```text
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2589`
```text
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_Shells.f90:3730`
```text
&                    cooling_curvature, &
&                    density_anomaly, &
&                    dQdTdA, elev, &
&                    fPSfer, gMean, gradie, &
&                    iConve, iPAfri, iPVRef, iUnitM, iUnitT, &
&                    LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, &
&                    mxEl, mxNode, &
```

`src/MOD_Shells.f90:3755`
```text
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
REAL*8, INTENT(IN) :: cooling_curvature, &                                             ! input
				   & density_anomaly, dQdTdA, elev, &                                 ! input
				   & fPSfer, gMean, gradie                                            ! input
INTEGER, INTENT(IN) :: iConve, iPAfri, iPVRef, iUnitM, iUnitT, mxEl, mxNode            ! input
INTEGER, INTENT(IN) :: LRn                                                             ! input
REAL*8, INTENT(IN) :: LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep       ! input
```

`src/MOD_Shells.f90:3898`
```text
!                spreading ridge.
!                The correct way is to set curviness(m, i) to make the
!                geotherm of each integration point arrive at
!                temperature tAsthK = tAdiab + gradie * 100.D3
!                at depth (in lithosphere) of
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------
```

`src/MOD_Shells.f90:3903`
```text
!                (zMoho(M,I)+tLInt(M,I)).
!      -----------------------------------------------------------------

tAsthK = tAdiab + gradie * 100.0D3

geoth1 = tSurf
geoth3 = -0.5D0 * radio(1) / conduc(1)
```

`src/MOD_Shells.f90:3996`
```text
!  Compute strength of shearing layer in asthenosphere:

CALL OneBar (continuum_LRi, &                                                   ! input
&              geothC, geothM, gradie, &                                          ! input
&              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&              mxEl, numEl, oneKm, tAdiab, &                                      ! input
&              zBAsth, zMoho, &                                                   ! input
```

`src/MOD_Shells.f90:5593`
```text
!                    *(1. - Byerly * offset(i) / offMax).
!    This may also be a pore pressure effect, because Byerlee's model is
!    that gouge layers have thickness in proportion to offset, and
!    that they support non-Darcy static pore pressure gradients which
!    allow elevated pore pressures in the core of the gouge, which
!    reduce the effective friction of the fault.

```

`src/MOD_Shells.f90:5735`
```text
&                       (0.50D0 * zTranF(1, i)**2 + zTranF(2, i) * zman + &
&                        0.50D0 * zTranF(2, i)**2)
		 END IF
!                dDPNdZ is the gradient of excess normal pressure (in
!                excess of vertical pressure) with depth on this fault;
!                check that it lies within frictional limits of blocks:
		 q = 0.250D0 * (dQdTdA(n1) + dQdTdA(n2) + &
```

`src/MOD_Shells.f90:6230`
```text
END SUBROUTINE OldVel

SUBROUTINE OneBar (continuum_LRi, &                                                   ! input
&                    geothC, geothM, gradie, &                                          ! input
&                    LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&                    mxEl, numEl, oneKm, tAdiab, &                                      ! input
&                    zBAsth, zMoho, &                                                   ! input
```

`src/MOD_Shells.f90:6242`
```text
IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
INTEGER, INTENT(IN) :: continuum_LRi                                                   ! input
REAL*8, INTENT(IN) :: geothC, geothM, gradie                                           ! input
INTEGER, INTENT(IN) :: LRn                                                             ! input
REAL*8, INTENT(IN) :: LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep       ! input
INTEGER, INTENT(IN) :: mxEl, numEl                                                     ! input
```

`src/MOD_Shells.f90:6301`
```text
&                   + gt(2) * z &
&                   + gt(3) * z * z &
&                   + gt(4) * z * z * z
			  ta = tAdiab + z * gradie
			  t = MIN(tg, ta)
			  t = MAX(t, 200.0D0)
			  bi = (t_bCreep(layer) + t_cCreep(layer) * z) * ecini
```

`src/OrbData5.f90:294`
```text
!      from the asthenosphere adiabat in the parameter file,
!      evaluated at (rather arbitrarily) 100 km depth:

       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

!   Read finite-element grid on unit 2:

```

`src/SHELLS_v5.0.f90:680`
```text
     &              cooling_curvature, &
     &              density_anomaly, &
     &              dQdTdA, elev, &
     &              fPSfer, gMean, gradie, &
     &              iConve, iPAfri, iPVRef, iUnitM, iUnitLog, &
     &              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, &
     &              mxEl, mxNode, &
```

`src/ShellSetMain.f90:584`
```text
    call ReadPm (     1, iUnitVerb, names,  nPlate, offMax, & ! INTENT(IN)
      &          aCreep, alphaT,    bCreep, Biot  , Byerly, & ! INTENT(OUT)
      &          cCreep, cFric,     conduc, dCreep, eCreep, &
      &          everyP, fFric,     gMean , gradie, iConve, &
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
      &          radio , radius,    refStr, rhoAst, rhoBar, &
      &          rhoH2O, TAdiab,    tauMax, temLim, title3, &
```

`src/ShellSetMain.f90:609`
```text

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
```

`src/ShellSetMain.f90:773`
```text
          if(ThID==1 .and. Verbose) write(iUnitVerb,'(A)') 'UpVar.in file detected, updating listed variables'
          call IterVar(fFric, cFric,  Biot,   Byerly, aCreep, &
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
        end if
```

### `ZBASTH`

`INPUT/iEarth5-049.in:12`
```text
5.E8,5.E8       dCreep = maximum shear stress at any temperature/strain-rate, Pa, crust/mantle
0.333333        eCreep = exponent on strain-rate in creep-strength law, = 1/n, same for crust & mantle
1412.,6.1E-4    tAdiab, gradie = intercept (in K) and slope (in K/m) of upper mantle adiabat
400.E3          zBAsth = depth (in m) of base of upper mantle (end of olivine=rich layer)
AF              pltRef = plate held fixed in boundary conditions (or reference frame in global model)
0,1.00 	        iConve, vTimes = convection under lithosphere (codes 0:6 given below, vTimes needed for iConve > 0; also see trHMax below)
0.0             trHMax = upper limit on basal tractions from mantle convection (in Pa; may be 0.0 for free-slip, regardless of iConve)
```

`src/MOD_SharedVars.f90:46`
```text
        & offMax, okDelV, okToQt, omega, oneKm, &
        & radio, radius, refStr, rhoAst, rhoBar, rhoH2O, &
        & slide, subDip, tAdiab, tauMax, temLim, trHMax, tSurf, &
        & vTimes, visMax, wedge, zBAsth

dimension alphaT(2), conduc(2), &
        & aCreep(2), bCreep(2), cCreep(2), dCreep(2), & ! default d_XXXX(1:2) = LR_set_XXXX(1:2, 0)
```

`src/MOD_ShellSet.f90:157`
```text
  & trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  & trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  & trim(VarNames(i)) /= 'eCreep' .AND. trim(VarNames(i)) /= 'tAdiab' .AND. trim(VarNames(i)) /= 'gradie' .AND. &
  & trim(VarNames(i)) /= 'zBAsth' .AND. trim(VarNames(i)) /= 'pltRef' .AND. trim(VarNames(i)) /= 'iConve' .AND. &
  & trim(VarNames(i)) /= 'trHMax' .AND. trim(VarNames(i)) /= 'tauMax' .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  & trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O' .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  & trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst' .AND. trim(VarNames(i)) /= 'gMean' .AND. &
```

`src/MOD_ShellSet.f90:229`
```text
  &  trim(VarNames(i)) /= 'bCreep_C' .AND. trim(VarNames(i)) /= 'bCreep_M' .AND. trim(VarNames(i)) /= 'cCreep_C' .AND. &
  &  trim(VarNames(i)) /= 'cCreep_M' .AND. trim(VarNames(i)) /= 'dCreep_C' .AND. trim(VarNames(i)) /= 'dCreep_M' .AND. &
  &  trim(VarNames(i)) /= 'eCreep'   .AND. trim(VarNames(i)) /= 'tAdiab'   .AND. trim(VarNames(i)) /= 'gradie'   .AND. &
  &  trim(VarNames(i)) /= 'zBAsth'   .AND. trim(VarNames(i)) /= 'pltRef'   .AND. trim(VarNames(i)) /= 'iConve'   .AND. &
  &  trim(VarNames(i)) /= 'trHMax'   .AND. trim(VarNames(i)) /= 'tauMax'   .AND. trim(VarNames(i)) /= 'tauMax_S' .AND. &
  &  trim(VarNames(i)) /= 'tauMax_L' .AND. trim(VarNames(i)) /= 'rhoH2O'   .AND. trim(VarNames(i)) /= 'rhoBar_C' .AND. &
  &  trim(VarNames(i)) /= 'rhoBar_M' .AND. trim(VarNames(i)) /= 'rhoAst'   .AND. trim(VarNames(i)) /= 'gMean'    .AND. &
```

`src/MOD_ShellSet.f90:534`
```text
      frmt = trim(frmt)//"X,F12.6,"
    case('gradie')
      frmt = trim(frmt)//"X,ES12.5,"
    case('zBAsth')
      frmt = trim(frmt)//"X,ES12.5,"
    case('trHMax')
      frmt = trim(frmt)//"X,ES12.5,"
```

`src/MOD_ShellSet.f90:1059`
```text
do while(.not. OData .and. i <= size(VarNames))
  if(trim(VarNames(i)) == 'tAdiab')   OData = .True.
  if(trim(VarNames(i)) == 'gradie')   OData = .True.
  if(trim(VarNames(i)) == 'zBAsth')   OData = .True.
  if(trim(VarNames(i)) == 'trHMax')   OData = .True.
  if(trim(VarNames(i)) == 'rhoH2O')   OData = .True.
  if(trim(VarNames(i)) == 'rhoBar_C') OData = .True.
```

`src/MOD_ShellSet.f90:1082`
```text

subroutine Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, & ! Update variable values with user input values
                        &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                        &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                        &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                        &  alphaT  , conduc, radio , tSurf , temLim, &
                        &  VarNames,VarValues)
```

`src/MOD_ShellSet.f90:1090`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(:),intent(in) :: VarNames
```

`src/MOD_ShellSet.f90:1131`
```text
      tAdiab = VarValues(i)
    case('gradie')
      gradie = VarValues(i)
    case('zBAsth')
      zBAsth = VarValues(i)
    case('trHMax')
      trHMax = VarValues(i)
```

`src/MOD_ShellSet.f90:1132`
```text
    case('gradie')
      gradie = VarValues(i)
    case('zBAsth')
      zBAsth = VarValues(i)
    case('trHMax')
      trHMax = VarValues(i)
    case('tauMax')
```

`src/MOD_ShellSet.f90:1184`
```text

subroutine IterVar(fFric, cFric,  Biot,   Byerly, aCreep, & ! Update variable values between 1st & 2nd Shells call
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)

```

`src/MOD_ShellSet.f90:1191`
```text
real*8,intent(inout) :: alphaT(2) , conduc(2) , fFric  , cFric  , Biot   , Byerly , &
                     &  aCreep(2) , bCreep(2) , eCreep , gMean  , gradie , oneKm   , &
                     &  cCreep(2) , dCreep(2) , radius , rhoAst , rhoH2O , tAdiab  , &
                     &  rhoBar(2) , temLim(2) , trHMax , tSurf  , zBAsth  , &
                     &  tauMax(2) , radio(2)

character(len=10),dimension(1) :: UpName
```

`src/MOD_ShellSet.f90:1218`
```text
  
  call Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, &
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
                    &  UpName,UpVal)
```

`src/MOD_ShellSet.f90:2426`
```text
&                    maxItr, okDelV, okToQt, oneKm,  radio,  &
&                    radius, refStr, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, tauMax, temLim, title3, &
&                    trHMax, tSurf,  vTimes, zBAsth, pltRef)



```

`src/MOD_ShellSet.f90:2446`
```text
       REAL*8, INTENT(OUT) :: okDelV, okToQt, oneKm,  radio, radius, refStr, &                ! output
          & rhoAst, rhoBar, rhoH2O, tAdiab, tauMax, temLim                                    ! output
       CHARACTER*100, INTENT(OUT) :: title3                                                    ! output
       REAL*8, INTENT(OUT) :: trHMax, tSurf,  vTimes, zBAsth                                  ! output
     ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
       CHARACTER*2,intent(out) :: pltRef
       INTEGER i, ios
```

`src/MOD_ShellSet.f90:2593`
```text
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) zBAsth
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
```

`src/MOD_ShellSet.f90:2594`
```text
       END IF

       READ (iunit7, * ) zBAsth
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
```

`src/MOD_ShellSet.f90:2595`
```text

       READ (iunit7, * ) zBAsth
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
```

`src/MOD_ShellSet.f90:2597`
```text
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2598`
```text
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

```

`src/MOD_ShellSet.f90:2614`
```text
  956  CONTINUE
       IF (iPVRef == 0) THEN
          write(ErrorMsg,'(A/,A/,A)') "ERROR in parameter input file: ",&
          &  "In line 13 (after zBAsth, before iConve), in the first two columns of the line,",&
          &  "define the velocity reference frame by entering one of the following plate names:"
          allocate(ErrorArrayChar(numPlt))
          ErrorArrayChar = names
```

`src/MOD_Shells.f90:3738`
```text
&                    nPlate, numEl, numNod, omega, oneKm, &
&                    radio, radius, rhoAst, rhoBar, rhoH2O, &
&                    tAdiab, temLim, tLNode, trHMax, tSurf, &
&                    vTimes, whichP, xNode, yNode, zBAsth, &
&                    zMNode, &
&                    contin, curviness, delta_rho, geothC, geothM, glue, & ! output
&                    oVB, pulled, sigZZI, &
```

`src/MOD_Shells.f90:3765`
```text
				   & tAdiab, temLim, tLNode, trHMax, tSurf, vTimes                    ! input
INTEGER, INTENT(IN) :: whichP                                                          ! input
REAL*8, INTENT(IN) :: xNode, yNode                                                     ! input
REAL*8, INTENT(IN) :: zBAsth, zMNode                                                   ! input
LOGICAL, INTENT(OUT) :: contin                                                         ! output
REAL*8, INTENT(OUT) :: curviness, delta_rho, geothC, geothM, glue, oVB                 ! output
LOGICAL, INTENT(OUT) :: pulled                                                         ! output
```

`src/MOD_Shells.f90:3999`
```text
&              geothC, geothM, gradie, &                                          ! input
&              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&              mxEl, numEl, oneKm, tAdiab, &                                      ! input
&              zBAsth, zMoho, &                                                   ! input
&              glue)                                                              ! output


```

`src/MOD_Shells.f90:6233`
```text
&                    geothC, geothM, gradie, &                                          ! input
&                    LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&                    mxEl, numEl, oneKm, tAdiab, &                                      ! input
&                    zBAsth, zMoho, &                                                   ! input
&                    glue)                                                              ! output

!   Calculates "glue" (shear stress required to create one unit of relative
```

`src/MOD_Shells.f90:6237`
```text
&                    glue)                                                              ! output

!   Calculates "glue" (shear stress required to create one unit of relative
!   horizontal velocity across the lithosphere+asthenosphere mantle layer, down to depth zBAsth).

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

`src/MOD_Shells.f90:6246`
```text
INTEGER, INTENT(IN) :: LRn                                                             ! input
REAL*8, INTENT(IN) :: LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep       ! input
INTEGER, INTENT(IN) :: mxEl, numEl                                                     ! input
REAL*8, INTENT(IN) :: oneKm, tAdiab, zBAsth, zMoho                                     ! input
REAL*8, INTENT(OUT) :: glue                                                            ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
INTEGER i, layer, level, limit, m
```

`src/MOD_Shells.f90:6263`
```text
DIMENSION ailog(2), gt(4)

dz = oneKm
limit = zBAsth / dz + 0.5D0
DO 100 i = 1, numEl
   !retrieve desired rheology for this continuum element:
	LRi = continuum_LRi(i)
```

`src/SHELLS_v5.0.f90:688`
```text
     &              nPlate, numEl, numNod, omega, oneKm, &
     &              radio, radius, rhoAst, rhoBar, rhoH2O, &
     &              tAdiab, temLim, tLNode, trHMax, tSurf, &
     &              vTimes, whichP, xNode, yNode, zBAsth, &
     &              zMNode, &
     &              contin, curviness, delta_rho, geothC, geothM, glue, & ! output
     &              oVB, pulled, sigZZI, &
```

`src/ShellSetMain.f90:588`
```text
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
      &          radio , radius,    refStr, rhoAst, rhoBar, &
      &          rhoH2O, TAdiab,    tauMax, temLim, title3, &
      &          trHMax, TSurf,     vTimes, zBAsth, pltRef)
    close(1)

    Run = .True.
```

`src/ShellSetMain.f90:609`
```text

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
```

`src/ShellSetMain.f90:773`
```text
          if(ThID==1 .and. Verbose) write(iUnitVerb,'(A)') 'UpVar.in file detected, updating listed variables'
          call IterVar(fFric, cFric,  Biot,   Byerly, aCreep, &
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
        end if
```

### `delta_rho_limit`

`src/MOD_Data.f90:212`
```text
       SUBROUTINE Assign (aArray,    aX1,    aDX,    aX2,    nAX,    aDY,    aY2,    nAY, & ! INTENT(IN)
     &                    alphaT, cLimit, conduc, &                                         ! INTENT(IN)
     &                    cArray,    cX1,    cDX,    cX2,    nCX,    cDY,    cY2,    nCY, & ! INTENT(IN)
     &                    delta_rho_limit, &                                                ! INTENT(IN)
     &                    eArray,    eX1,    eDX,    eX2,    nEX,    eDY,    eY2,    nEY, & ! INTENT(IN)
     &                     gMean,  hCMax,  hLMax, &                                         ! INTENT(IN)
     &                    iUnitL, iUnitT, &                                                 ! INTENT(IN)
```

`src/MOD_Data.f90:259`
```text
       REAL*8, INTENT(IN) :: aArray,    aX1,    aDX,    aX2,    aDY,    aY2, &
                           & alphaT, cLimit, conduc, &
                           & cArray,    cX1,    cDX,    cX2,    cDY,    cY2, &
                           & delta_rho_limit, &
                           & eArray,    eX1,    eDX,    eX2,    eDY,    eY2, &
                           &  gMean,  hCMax,  hLMax, &
                           &  oneKm, &
```

`src/MOD_Data.f90:719`
```text

!   Apply limits:

       chemical_delta_rho = MIN(chemical_delta_rho,  delta_rho_limit)
       chemical_delta_rho = MAX(chemical_delta_rho, -delta_rho_limit)

!   Repeat isostasy test:
```

`src/MOD_Data.f90:720`
```text
!   Apply limits:

       chemical_delta_rho = MIN(chemical_delta_rho,  delta_rho_limit)
       chemical_delta_rho = MAX(chemical_delta_rho, -delta_rho_limit)

!   Repeat isostasy test:

```

`src/OrbData5.f90:184`
```text
!    transition zone, where new mineral phases appear,
!    and the input physical parameters would therefore not be valid.

!   "delta_rho_limit" is the maximum permitted size of chemical
!    density anomalies throughout the lithosphere:
       REAL*8,PARAMETER :: delta_rho_limit = 100.0D0 ! units of (kilogram per cubic meter)

```

`src/OrbData5.f90:186`
```text

!   "delta_rho_limit" is the maximum permitted size of chemical
!    density anomalies throughout the lithosphere:
       REAL*8,PARAMETER :: delta_rho_limit = 100.0D0 ! units of (kilogram per cubic meter)

!  Note that all of the above are in SI units (W/m**2, m, m, m,
!      kg/m**3, etc.)
```

`src/OrbData5.f90:274`
```text
!    Echo the limits that are compiled-in-place, for a complete record:

       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
    5  FORMAT(/' The following limits apply in this run:' &
```

`src/OrbData5.f90:276`
```text
       IF(Verbose) WRITE (iUnitVerb, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
       WRITE (iUnitL, 5) qLim0, dQL_dE, qLim1, cLimit, hCMax, hLMax, &
     &                  delta_rho_limit
    5  FORMAT(/' The following limits apply in this run:' &
     &/'    Lower limit on heat-flow = ', F5.3, '+', ES10.3, ' * elevation' &
     &/'    Upper limit on heat-flow = ', F5.3 &
```

`src/OrbData5.f90:529`
```text
            CALL Assign (aArray,    aX1,    aDX,    aX2,    nAX,    aDY,    aY2,    nAY, & ! INTENT(IN)
     &                   alphaT, cLimit, conduc, &                                         ! INTENT(IN)
     &                   cArray,    cX1,    cDX,    cX2,    nCX,    cDY,    cY2,    nCY, & ! INTENT(IN)
     &                   delta_rho_limit, &                                                ! INTENT(IN)
     &                   eArray,    eX1,    eDX,    eX2,    nEX,    eDY,    eY2,    nEY, & ! INTENT(IN)
     &                    gMean,  hCMax,  hLMax, &                                         ! INTENT(IN)
     &                   iUnitL, iUnitVerb, &                                                 ! INTENT(IN)
```

## Parameter readers, bindings and call sites

`src/MOD_Data.f90:79`; nearby symbols: alphaT, temLim
```text
       REAL*8, INTENT(OUT) :: tauZZ, sigZZB
!   Argument arrays:
       DIMENSION alphaT(2), rhoBar(2), temLim(2)

       INTEGER, PARAMETER :: nDRef = 300
       INTEGER :: i, j, lastDR, layer1, layer2, n1, n2, nStep
       LOGICAL :: called =.FALSE.
       REAL*8 :: dense, dense1, dense2, frac, frac1, frac2, h, &
               & oldPr, oldSZZ, Pr, resid, rhoTop, sigZZ, T, z, zBase, zTop
```

`src/MOD_Data.f90:114`; nearby symbols: alphaT
```text
                 PRef(i) = PRef(i - 1) + dRef(i) * gMean * oneKm
  100       CONTINUE
       END IF

!   Routine processing (in every CALL):

       IF (elevat > 0.0D0) THEN
!        Land:
            zTop = -elevat
```

`src/MOD_Data.f90:705`; nearby symbols: alphaT, conduc, temLim
```text

       chemical_delta_rho = 0.0D0
!     (Try this case first; adjust density_anomaly below.)

       CALL Squeez (alphaT, chemical_delta_rho, elevat, & ! INTENT(IN)
     &              geoth1, geoth2, geoth3, geoth4, &     ! INTENT(IN)
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &               gMean, iUnitT, &                     ! INTENT(IN)
     &               oneKm, rhoAst, rhoBar, rhoH2O, &     ! INTENT(IN)
```

`src/MOD_Data.f90:724`; nearby symbols: alphaT, temLim, delta_rho_limit
```text
       chemical_delta_rho = MAX(chemical_delta_rho, -delta_rho_limit)

!   Repeat isostasy test:

       CALL Squeez (alphaT, chemical_delta_rho, elevat, & ! INTENT(IN)
     &              geoth1, geoth2, geoth3, geoth4, &     ! INTENT(IN)
     &              geoth5, geoth6, geoth7, geoth8, &     ! INTENT(IN)
     &              gMean, iUnitT, &                      ! INTENT(IN)
     &              oneKm, rhoAst, rhoBar, rhoH2O, &      ! INTENT(IN)
```

`src/MOD_Data.f90:2003`; nearby symbols: dQdTdA
```text
            elev(i) = elevi
            dQdTdA(i) = qi
            IF (qi < 0.0D0) THEN
			  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
			  call FatalError(ErrorMsg,ThID)
            END IF
            IF (.NOT.brief) THEN
                 IF(Verbose) WRITE (iUnitT, 99) INDEX, pLon, pLat, xi, yi, elevi, qi
   99            FORMAT (' ', I10, 2F12.3, 2F11.5, 2ES10.2)
```

`src/MOD_Score.f90:1085`; nearby symbols: dQdTdA
```text
     &                    numEl, numNod, n1000, offMax, offset, &
     &                    title1, tLNode, xNode, yNode, zMNode, &
     &                    checkE, checkF, checkN)     ! work

!   Read finite element grid from unit iUnit7 (assumed already OPENed).
!   Echoes the important values to unit iUnitT (assumed already OPENed).

       IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

`src/MOD_Score.f90:1211`; nearby symbols: dQdTdA
```text
            elev(i) = elevi
            dQdTdA(i) = qi
            IF (qi < 0.0D0) THEN
			  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
			  call FatalError(ErrorMsg,ThID)
            END IF
            IF (zmi < 0.0D0) THEN
			  write(ErrorMsg,'(A)') "NEGATIVE CRUSTAL THICKNESS IS NON-PHYSICAL."
			  call FatalError(ErrorMsg,ThID)
```

`src/MOD_SharedVars.f90:34`; nearby symbols: alphaT, conduc
```text
integer :: ThID
character(len=100) :: title1, title2, title3
logical :: Verbose, everyP
integer,parameter :: iUnitVerb = 6 ! Unit number for optional verbose.txt file
integer,parameter :: iUnitOrbDat = 66 ! Unit number for OrbScore misfits scores during misfit convergence

integer,parameter :: nPlate = 52 ! Number of pLates in PB2002 model of Bird [2003]
integer :: iConve,iPVRef,maxItr
character(len=2) :: pltRef
```

`src/MOD_SharedVars.f90:36`; nearby symbols: alphaT, conduc, GRADIE
```text
logical :: Verbose, everyP
integer,parameter :: iUnitVerb = 6 ! Unit number for optional verbose.txt file
integer,parameter :: iUnitOrbDat = 66 ! Unit number for OrbScore misfits scores during misfit convergence

integer,parameter :: nPlate = 52 ! Number of pLates in PB2002 model of Bird [2003]
integer :: iConve,iPVRef,maxItr
character(len=2) :: pltRef

real*8 :: alphaT, conduc, constr, &
```

`src/MOD_ShellSet.f90:1182`; nearby symbols: alphaT, conduc, TSurf, temLim, TADIAB, GRADIE, ZBASTH
```text

end subroutine


subroutine IterVar(fFric, cFric,  Biot,   Byerly, aCreep, & ! Update variable values between 1st & 2nd Shells call
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim)
```

`src/MOD_ShellSet.f90:1216`; nearby symbols: alphaT, conduc, TSurf, temLim, TADIAB, GRADIE, ZBASTH
```text
  end if
	  	
  if(Verbose) write(iUnitVerb,"(3A)") "Updating ",trim(UpName(1))," with new value from UpVar.in."
  
  call Variable_Update(fFric   , cFric , Biot  , Byerly, aCreep, &
                    &  bCreep  , cCreep, dCreep, eCreep, tAdiab, &
                    &  gradie  , zBAsth, trHMax, tauMax, rhoH2O, &
                    &  rhoBar  , rhoAst, gMean , oneKm , radius, &
                    &  alphaT  , conduc, radio , tSurf , temLim, &
```

`src/MOD_ShellSet.f90:2418`; nearby symbols: alphaT, conduc, GRADIE
```text
!------------------------------------------------------------------------------
! From Original Program Units
!------------------------------------------------------------------------------

SUBROUTINE ReadPm (iUnit7, iUnitT, names , numPlt, offMax, & ! Read parameter input file
&                    aCreep, alphaT, bCreep, Biot  , &         ! output
&                    Byerly, cCreep, cFric , conduc, &
&                    dCreep, eCreep, everyP, fFric , gMean , &
&                    gradie, iConve, iPVRef, &
```

`src/MOD_ShellSet.f90:2456`; nearby symbols: alphaT, conduc, temLim
```text
     &           dCreep(2), names(numplt), radio(2), &
     &           rhoBar(2), tauMax(2), temLim(2), tempv(2), vector(2)

       IF(Verbose) WRITE(iUnitT,1) iunit7
    1  FORMAT(//' Attempting to read input parameter file from unit ', I3/)
       title3 = ' '
       READ (iunit7, 2, IOSTAT = ios) title3
       IF (ios /= 0) THEN
          write(ErrorMsg,'(A)') "File not found, or file is empty, or file is too short."
```

`src/MOD_ShellSet.f90:2458`; nearby symbols: temLim
```text

       IF(Verbose) WRITE(iUnitT,1) iunit7
    1  FORMAT(//' Attempting to read input parameter file from unit ', I3/)
       title3 = ' '
       READ (iunit7, 2, IOSTAT = ios) title3
       IF (ios /= 0) THEN
          write(ErrorMsg,'(A)') "File not found, or file is empty, or file is too short."
          call FatalError(ErrorMsg,ThID)
       END IF
```

`src/MOD_ShellSet.f90:2580`; nearby symbols: TADIAB, GRADIE
```text
       IF(Verbose) WRITE (iUnitT, 90) eCreep
   90  FORMAT (' ',11X,F10.6,' eCreep = E for creep = strain-rate expo', &
     &           'nent for creep (1/n).  (Same for crust and mantle!)')
       IF (eCreep <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: eCreep must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tAdiab, gradie
```

`src/MOD_ShellSet.f90:2581`; nearby symbols: TADIAB, GRADIE
```text
   90  FORMAT (' ',11X,F10.6,' eCreep = E for creep = strain-rate expo', &
     &           'nent for creep (1/n).  (Same for crust and mantle!)')
       IF (eCreep <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: eCreep must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
```

`src/MOD_ShellSet.f90:2584`; nearby symbols: TADIAB, GRADIE
```text
         write(ErrorMsg,'(A)') "ERROR in parameter input file: eCreep must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tAdiab, gradie
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
```

`src/MOD_ShellSet.f90:2589`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
       IF(Verbose) WRITE (iUnitT, 92) tAdiab, gradie
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) zBAsth
```

`src/MOD_ShellSet.f90:2590`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
   92  FORMAT (' ',F10.0,' ',1P,E10.2,' tAdiab, GRADIE = intercept and ' &
     &        ,'slope of upper mantle adiabat below plate (K, K/m)')
       IF ((tAdiab < 0.0D0).OR.(gradie < 0.0D0)) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) zBAsth
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
```

`src/MOD_ShellSet.f90:2593`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
         write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative Kelvin temperature and/or negative adiabatic gradient is/are unphysical."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) zBAsth
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
```

`src/MOD_ShellSet.f90:2598`; nearby symbols: ZBASTH
```text
       IF(Verbose) WRITE (iUnitT, 94) zBAsth
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, 952) pltRef
```

`src/MOD_ShellSet.f90:2599`; nearby symbols: ZBASTH
```text
   94  FORMAT (' ',11X,1P,E10.2,' zBAsth = depth of base of', &
     &                          ' asthenosphere')
       IF (zBAsth <= 0.0D0) THEN
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, 952) pltRef
  952  FORMAT(A2)
```

`src/MOD_ShellSet.f90:2602`; nearby symbols: ZBASTH
```text
         write(ErrorMsg,'(A)') "ERROR in parameter input file: zBAsth must be positive."
         call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, 952) pltRef
  952  FORMAT(A2)
       IF(Verbose) WRITE (iUnitT, 954) pltRef
  954  FORMAT(' ',A2,'<==================', &
     &        ' pltRef = plate defining velocity ', &
```

`src/MOD_ShellSet.f90:2613`; nearby symbols: ZBASTH
```text
       DO 956 i = 1, numPlt
            IF (names(i) == pltRef) iPVRef = i
  956  CONTINUE
       IF (iPVRef == 0) THEN
          write(ErrorMsg,'(A/,A/,A)') "ERROR in parameter input file: ",&
          &  "In line 13 (after zBAsth, before iConve), in the first two columns of the line,",&
          &  "define the velocity reference frame by entering one of the following plate names:"
          allocate(ErrorArrayChar(numPlt))
          ErrorArrayChar = names
```

`src/MOD_ShellSet.f90:2618`; nearby symbols: ZBASTH
```text
          &  "In line 13 (after zBAsth, before iConve), in the first two columns of the line,",&
          &  "define the velocity reference frame by entering one of the following plate names:"
          allocate(ErrorArrayChar(numPlt))
          ErrorArrayChar = names
          call FatalError(ErrorMsg,ThID,ErrArrCh=ErrorArrayChar)
       END IF

       READ (iunit7, * ) iConve
       IF(Verbose) WRITE (iUnitT, 96) iConve
```

`src/MOD_ShellSet.f90:2734`; nearby symbols: alphaT
```text
       READ (iunit7, * ) radius
       IF(Verbose) WRITE (iUnitT, 155) radius
  155  FORMAT (' ',11X,1P,E10.3,' radius = radius of the planet')
       IF (radius <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: radius must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
```

`src/MOD_ShellSet.f90:2735`; nearby symbols: alphaT
```text
       IF(Verbose) WRITE (iUnitT, 155) radius
  155  FORMAT (' ',11X,1P,E10.3,' radius = radius of the planet')
       IF (radius <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: radius must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             alphaT)              ! output
```

`src/MOD_ShellSet.f90:2738`; nearby symbols: alphaT
```text
          write(ErrorMsg,'(A)') "ERROR in parameter input file: radius must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             alphaT)              ! output
       IF(Verbose) WRITE (iUnitT, 160) alphaT(1), alphaT(2)
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
```

`src/MOD_ShellSet.f90:2745`; nearby symbols: alphaT, conduc
```text
  160  FORMAT (' ',1P,E10.2,' ',E10.2,' alphaT = volumetric thermal', &
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
       IF ((alphaT(1) < 0.0D0).OR.(alphaT(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative alphaT in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
```

`src/MOD_ShellSet.f90:2746`; nearby symbols: alphaT, conduc
```text
     &                                ' expansion', &
     &            ' (1/V)*(dV/dT). (crust/mantle)')
       IF ((alphaT(1) < 0.0D0).OR.(alphaT(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative alphaT in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             conduc)              ! output
```

`src/MOD_ShellSet.f90:2749`; nearby symbols: alphaT, conduc
```text
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative alphaT in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             conduc)              ! output
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
```

`src/MOD_ShellSet.f90:2755`; nearby symbols: conduc
```text
       IF(Verbose) WRITE (iUnitT, 170) conduc(1), conduc(2)
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
```

`src/MOD_ShellSet.f90:2756`; nearby symbols: conduc
```text
  170  FORMAT (' ',1P,E10.2,' ',E10.2,' conduc = thermal conductivity,', &
     &        ' energy/length/s/deg. (crust/mantle)')
       IF ((conduc(1) <= 0.0D0).OR.(conduc(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             radio)               ! output
```

`src/MOD_ShellSet.f90:2759`; nearby symbols: conduc
```text
          write(ErrorMsg,'(A)') "ERROR in parameter input file: conduc must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             radio)               ! output
       IF(Verbose) WRITE (iUnitT, 180) radio(1), radio(2)
  180  FORMAT (' ',1P,E10.2,' ',E10.2,' radio  = radioactive heat ', &
     &        'production, energy/volume/s. (crust/mantle)')
```

`src/MOD_ShellSet.f90:2765`; nearby symbols: TSurf
```text
       IF(Verbose) WRITE (iUnitT, 180) radio(1), radio(2)
  180  FORMAT (' ',1P,E10.2,' ',E10.2,' radio  = radioactive heat ', &
     &        'production, energy/volume/s. (crust/mantle)')
       IF ((radio(1) < 0.0D0).OR.(radio(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative radio in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tSurf
```

`src/MOD_ShellSet.f90:2766`; nearby symbols: TSurf
```text
  180  FORMAT (' ',1P,E10.2,' ',E10.2,' radio  = radioactive heat ', &
     &        'production, energy/volume/s. (crust/mantle)')
       IF ((radio(1) < 0.0D0).OR.(radio(2) < 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative radio in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tSurf
       IF(Verbose) WRITE (iUnitT, 185) tSurf
```

`src/MOD_ShellSet.f90:2769`; nearby symbols: TSurf
```text
          write(ErrorMsg,'(A)') "ERROR in parameter input file: Negative radio in either layer is unphysical."
          call FatalError(ErrorMsg,ThID)
       END IF

       READ (iunit7, * ) tSurf
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
```

`src/MOD_ShellSet.f90:2774`; nearby symbols: TSurf, temLim
```text
       IF(Verbose) WRITE (iUnitT, 185) tSurf
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
```

`src/MOD_ShellSet.f90:2775`; nearby symbols: TSurf, temLim
```text
  185  FORMAT (' ',11X,F10.0,' tSurf  = surface temperature, on', &
     &        ' absolute scale (deg. K)')
       IF (tSurf <= 0.0D0) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             temLim)              ! output
```

`src/MOD_ShellSet.f90:2778`; nearby symbols: TSurf, temLim
```text
          write(ErrorMsg,'(A)') "ERROR in parameter input file: tSurf must be positive."
          call FatalError(ErrorMsg,ThID)
       END IF

       CALL ReadN (iunit7, iUnitT, 2, & ! input
     &             temLim)              ! output
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
```

`src/MOD_ShellSet.f90:2784`; nearby symbols: temLim
```text
       IF(Verbose) WRITE (iUnitT, 190) temLim(1), temLim(2)
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: temLim must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

       IF(Verbose) WRITE (iUnitT, 199)
```

`src/MOD_ShellSet.f90:2785`; nearby symbols: temLim
```text
  190  FORMAT (' ',F10.0,' ',F10.0,' temLim = convecting', &
     &       ' temperature (Tmax), on absolute scale. (crust/mantle)')
       IF ((temLim(1) <= 0.0D0).OR.(temLim(2) <= 0.0D0)) THEN
          write(ErrorMsg,'(A)') "ERROR in parameter input file: temLim must be positive in each layer."
          call FatalError(ErrorMsg,ThID)
       END IF

       IF(Verbose) WRITE (iUnitT, 199)
  199  FORMAT (' [OMIT from iXXX.in]' &
```

`src/MOD_Shells.f90:762`; nearby symbols: dQdTdA, alphaT, conduc
```text
doFB1 = .FALSE.
doFB2 = .FALSE.
doFB3 = .FALSE.
doFB4 = .TRUE.
CALL Fixed (alphaT, area, conduc, &  ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
&             dXSP, dYSP, edgeTS, elev, fDip, fLen, fPFlt, &
```

`src/MOD_Shells.f90:886`; nearby symbols: dQdTdA, alphaT, conduc
```text
doFB1 = .FALSE.
doFB2 = .TRUE.
doFB3 = .FALSE.
doFB4 = .FALSE.
CALL Fixed (alphaT, area, conduc, &   ! input
&             density_anomaly, detJ, &
&             doFB1, doFB2, doFB3, doFB4, &
&             dQdTdA, dXS, dYS, &
&             dXSP, dYSP, edgeTS, elev, fDip, fLen, fPFlt, &
```

`src/MOD_Shells.f90:3719`; nearby symbols: alphaT, conduc
```text
CALL EDot (dXS, dYS, &  ! input
&            fPSfer, mxEl, &
&            mxNode, nodes, numEl, radius, sita, v, &
&            eRate)       ! output
CALL TauDef (alpha, eRate, mxEl, numEl, tOfset, & ! input
&              tauMat)                              ! output

RETURN
END SUBROUTINE FEM
```

`src/MOD_Shells.f90:3851`; nearby symbols: heatFl
```text
END IF

!   Same field expressed as values at integration points:

CALL Flow (fPSfer, mxEl, mxNode, nodes, numEl, vm, & ! input
&            oVB)                                      ! output

!   Decide which points are "continental"
!     (a distinction that matters only if iConve=4),
```

`src/MOD_Shells.f90:3859`; nearby symbols: heatFl, dQdTdA
```text
!     (a distinction that matters only if iConve=4),
!     using zMoho as temporary storage for interpolated elevation,
!     and tLInt as temporary storage for interpolated heatflow:

CALL Interp (elev, mxEl, mxNode, nodes, numEl, & ! input
&              zMoho)                              ! output
CALL Interp (dQdTdA, mxEl, mxNode, nodes, numEl, & ! input
&              tLInt)                                ! output
DO 2 m = 1, 7
```

`src/MOD_Shells.f90:3861`; nearby symbols: heatFl, dQdTdA
```text
!     and tLInt as temporary storage for interpolated heatflow:

CALL Interp (elev, mxEl, mxNode, nodes, numEl, & ! input
&              zMoho)                              ! output
CALL Interp (dQdTdA, mxEl, mxNode, nodes, numEl, & ! input
&              tLInt)                                ! output
DO 2 m = 1, 7
	DO 1 i = 1, numEl
		 contin(m, i) = (zMoho(m, i) > -2500.0D0).AND. &
```

`src/MOD_Shells.f90:3980`; nearby symbols: alphaT, conduc, temLim
```text
&           2.0D0 * geoth3 * zMNode(i) + &
&           3.0D0 * geoth4 * zMNode(i)**2
	geoth6 = dTdZC * conduc(1) / conduc(2)
	geoth7 = -0.50D0 * radio(2) / conduc(2) - 0.50D0 * cooling_curvature(i)
	CALL Squeez (alphaT, density_anomaly(i), elev(i), &  ! input
&                   geoth1, geoth2, geoth3, geoth4, &
&                   geoth5, geoth6, geoth7, geoth8, &
&                   gMean, &
&                   iUnitT, oneKm, rhoAst, rhoBar, rhoH2O, &
```

`src/MOD_Shells.f90:3988`; nearby symbols: temLim
```text
&                   iUnitT, oneKm, rhoAst, rhoBar, rhoH2O, &
&                   temLim, zMNode(i), zMNode(i) + tLNode(i), &
&                   tauZZN(i), atNode(i))                   ! output
100  CONTINUE
CALL Interp (atNode, mxEl, mxNode, nodes, numEl, & ! input
&              sigZZI)                               ! output
CALL Interp (tauZZN, mxEl, mxNode, nodes, numEl, & ! input
&              tauZZI)                               ! output

```

`src/MOD_Shells.f90:3990`; nearby symbols: temLim, GRADIE
```text
&                   tauZZN(i), atNode(i))                   ! output
100  CONTINUE
CALL Interp (atNode, mxEl, mxNode, nodes, numEl, & ! input
&              sigZZI)                               ! output
CALL Interp (tauZZN, mxEl, mxNode, nodes, numEl, & ! input
&              tauZZI)                               ! output

!  Compute strength of shearing layer in asthenosphere:

```

`src/MOD_Shells.f90:3995`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
&              tauZZI)                               ! output

!  Compute strength of shearing layer in asthenosphere:

CALL OneBar (continuum_LRi, &                                                   ! input
&              geothC, geothM, gradie, &                                          ! input
&              LRn, LR_set_aCreep, LR_set_bCreep, LR_set_cCreep, LR_set_eCreep, & ! input
&              mxEl, numEl, oneKm, tAdiab, &                                      ! input
&              zBAsth, zMoho, &                                                   ! input
```

`src/MOD_Shells.f90:4175`; nearby symbols: alphaT, conduc
```text
ELSE
  xPoint = 90.0D0 - xInPl * 57.2957795130823D0
  yPoint = yInPl * 57.2957795130823D0
  write(ErrorMsg,'(A,2F13.5,A)') "THE POINT ",xPoint, yPoint," DOES NOT BELONG ANY PLATE !!! Therefore plate velocity is undefined."
  call FatalError(ErrorMsg,ThID)
END IF
RETURN
END SUBROUTINE FindPV

```

`src/MOD_Shells.f90:4513`; nearby symbols: alphaT, conduc
```text
&                                             geoth3 * zm**2
								  geoth6 = (q - zm * radio(1)) / conduc(2)
								  geoth7 = -0.5D0 * radio(2) / conduc(2)
								  geoth8 = 0.0D0
								  CALL Squeez (alphaT, &      ! input
&                                                 delta_rho, &
&                                                 elevat, &
&                                                 geoth1, geoth2, &
&                                                 geoth3, geoth4, &
```

`src/MOD_Shells.f90:4685`; nearby symbols: dQdTdA
```text
&                    numEl, numNod, n1000, offMax, offset, &
&                    title1, tLNode, xNode, yNode, zMNode, &
&                    checkE, checkF, checkN)     ! work

!   Read finite element grid from unit iUnit7 (assumed already OPENed).
!   Echoes the important values to unit iUnitT (assumed already OPENed).

IMPLICIT NONE
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

`src/MOD_Shells.f90:4811`; nearby symbols: dQdTdA
```text
	elev(i) = elevi
	dQdTdA(i) = qi
	IF (qi < 0.0D0) THEN
	  write(ErrorMsg,'(A)') "NEGATIVE HEAT-FLOW IS NON-PHYSICAL."
	  call FatalError(ErrorMsg,ThID)
	END IF
	IF (zmi < 0.0D0) THEN
	  write(ErrorMsg,'(A)') "NEGATIVE CRUSTAL THICKNESS IS NON-PHYSICAL."
	  call FatalError(ErrorMsg,ThID)
```

`src/MOD_Shells.f90:6585`; nearby symbols: alphaT, conduc, temLim
```text
DIMENSION alphaT(2), conduc(2), &
&           radio(2),  rhoBar(2), temLim(2)

IF (lastPm /= 999) THEN
  write(ErrorMsg,'(A)') "WRONG NUMBER OF ARGUMENTS IN CALL TO -Pure-!"
  call FatalError(ErrorMsg,ThID)
END IF

!   Initialize strain rate and vertical integrals of relative stress
```

`src/MOD_Shells.f90:6586`; nearby symbols: alphaT, conduc, temLim
```text
&           radio(2),  rhoBar(2), temLim(2)

IF (lastPm /= 999) THEN
  write(ErrorMsg,'(A)') "WRONG NUMBER OF ARGUMENTS IN CALL TO -Pure-!"
  call FatalError(ErrorMsg,ThID)
END IF

!   Initialize strain rate and vertical integrals of relative stress
!   for the triangular continuum elements:
```

`src/MOD_Shells.f90:6606`; nearby symbols: alphaT
```text
		 tauMat(3, m, i) = 0.0D0
10       CONTINUE
20  CONTINUE

CALL Viscos (alphaT, &                              ! input
&              continuum_LRi, &
&              delta_rho, &
&              eRate, gMean, geothC, geothM, &
&              LRn, LR_set_cFric, LR_set_Biot, &
```

`src/MOD_Shells.f90:6617`; nearby symbols: temLim
```text
&              sigHB, tauMat, temLim, tLInt, &
&              visMax, zMoho, &
&              alpha, scoreC, scoreD, tOfset, zTranC) ! output

CALL TauDef (alpha, eRate, mxEl, numEl, tOfset, & ! input
&              tauMat)                              ! output

!   Initialize slip rate and vertical integrals of relative stress
!   for the linear fault elements
```

`src/MOD_Shells.f90:6629`; nearby symbols: dQdTdA, alphaT, conduc
```text
&                      zMNode(nodeF(2, i))) / 6.0D0
	zTranF(2, i) = (tLNode(nodeF(1, i)) + &
&                      tLNode(nodeF(2, i))) / 6.0D0
30  CONTINUE
CALL Mohr (alphaT, conduc, constr, &                     ! input
&            continuum_LRi, &
&            dQdTdA, elev, &
&            fault_LRi, fDip, fMuMax, &
&            fPFlt, fArg, gMean, &
```

`src/MOD_Shells.f90:6683`; nearby symbols: alphaT
```text
&                  mxEl, mxNode, nodes, numEl, &
&                  oVB, pulled, trHMax, v, &
&                  eta, sigHB, &                   ! output
&                  outVec)                         ! work
	CALL Viscos (alphaT, &                              ! input
&                   continuum_LRi, &
&                   delta_rho, &
&                   eRate, gMean, geothC, geothM, &
&                   LRn, LR_set_cFric, LR_set_Biot, &
```

`src/MOD_Shells.f90:6693`; nearby symbols: dQdTdA, alphaT, conduc, temLim
```text
&                   mxEl, numEl, rhoBar, rhoH2O, &
&                   sigHB, tauMat, temLim, tLInt, &
&                   visMax, zMoho, &
&                   alpha, scoreC, scoreD, tOfset, zTranC) ! output
	CALL Mohr (alphaT, conduc, constr, &                     ! input
&                 continuum_LRi, &
&                 dQdTdA, elev, &
&                 fault_LRi, fDip, fMuMax, &
&                 fPFlt, fArg, gMean, &
```

`src/MOD_Shells.f90:9094`; nearby symbols: temLim
```text
REAL*8, INTENT(OUT) :: tauzz, sigzzb                                                   ! output
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
REAL*8 TempC, TempM, h ! statement functions
!      - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
INTEGER, PARAMETER :: ndRef = 300
INTEGER i, j, lastDR, layer1, layer2, n1, n2, nStep
REAL*8 dense, dense1, dense2, dRef, frac, frac1, frac2, &
	& oldpr, oldszz, pr, pRef, resid, rhotop, sigzz, t, z, zBase, zTop
LOGICAL :: called = .FALSE.
```

`src/MOD_Shells.f90:9130`; nearby symbols: alphaT
```text
		 pRef(i) = pRef(i - 1) + dRef(i) * gMean * oneKm
100       CONTINUE
END IF

!   Routine processing (in every CALL):

IF (elevat > 0.0D0) THEN
!        Land:
	zTop = -elevat
```

`src/MOD_Shells.f90:10005`; nearby symbols: alphaT
```text
				   zOfTop = 0.0D0
				   pl0 = 0.0D0
				   pw0 = 0.0D0
				   rho_use = rhoBar(1) + delta_rho(m, i)
				   CALL Diamnd (t_aCreep(1), alphaT(1), & ! input
&                                  t_bCreep(1), t_Biot, &
&                                  t_cCreep(1), t_dCreep(1), &
&                                  t_eCreep, &
&                                  e1, e2, t_fric, g, &
```

`src/MOD_Shells.f90:10049`; nearby symbols: alphaT
```text
&                      0.25D0 * geothC(4, m, i) * thickC**3
				   rhoUse = rhoBar(1) * (1.0D0 - alphaT(1) * tMean)
				   pl0 = rhoUse * g * thickC
				   rho_use = rhoBar(2) + delta_rho(m, i)
				   CALL Diamnd (t_aCreep(2), alphaT(2), & ! input
&                                  t_bCreep(2), t_Biot, &
&                                  t_cCreep(2), t_dCreep(2), &
&                                  t_eCreep, &
&                                  e1, e2, t_fric, g, &
```

`src/OrbData5.f90:102`; nearby symbols: dQdTdA, qArray
```text
       REAL*8, DIMENSION(:, :), ALLOCATABLE :: eArray, qArray, aArray, &
     &                                         cArray, sArray, arcanaDomainArray, &
     &                                         arcanaLithosphereArray

!  DIMENSIONS using PARAMETER maxNod:
       DIMENSION checkN(maxNod), chemical_delta_rho_list(maxNod), &
     &           cooling_curvature_list(maxNod), dQdTdA(maxNod), &
     &           elev  (maxNod), &
     &           tLNode(maxNod), &
```

`src/OrbData5.f90:109`; nearby symbols: dQdTdA
```text
     &           elev  (maxNod), &
     &           tLNode(maxNod), &
     &           xNode (maxNod), yNode (maxNod), zMNode(maxNod)

!  DIMENSIONS using PARAMETER maxBN:
       DIMENSION nodCon(maxBN)

!  DIMENSIONS USING PARAMETER maxEl:
       DIMENSION area              (maxEl), checkE            (maxEl), &
```

`src/OrbData5.f90:155`; nearby symbols: qLim0, dQL_dE
```text
!-------------------------------------------------------------------
!                       DATA statements
!   "qLim0" is the lower limit on heat-flow for points
!      with an elevation of zero.
       REAL*8,PARAMETER :: qLim0 = 0.000D0 ! units of (watts per square meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)

```

`src/OrbData5.f90:162`; nearby symbols: qLim0, dQL_dE, qLim1
```text
!      DATA qLim0 /0.045D0/ ! units of (watts per square meter)

!   "dQL_dE" is the derivitive d(qLim0)/d(elevation),
!    which adjusts the minimum heat-flow for elevation.
       REAL*8,PARAMETER :: dQL_dE = 0.00D-06 ! units of (watts per square meter)/(meter)

!  [N.B. Former limit, in program OrbData, was:}
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)

```

`src/OrbData5.f90:168`; nearby symbols: dQL_dE, qLim1
```text
!  [N.B. Former limit, in program OrbData, was:}
!      DATA dQL_dE /1.43D-06/ ! units of (watts per square meter)/(meter)

!   "qLim1 is the upper limit on heat-flow for all points.
       REAL*8,PARAMETER :: qLim1 = 0.300D0 ! units of (watts per square meter)

!   "cLimit" is a lower-limit on crustal thickness:
       REAL*8,PARAMETER :: cLimit = 6570.0D0 ! meters
!    Changed from 5000. to 6570. on 2005.05.24, to agree with CRUST2.grd.
```

`src/OrbData5.f90:171`; nearby symbols: dQL_dE, qLim1
```text
!   "qLim1 is the upper limit on heat-flow for all points.
       REAL*8,PARAMETER :: qLim1 = 0.300D0 ! units of (watts per square meter)

!   "cLimit" is a lower-limit on crustal thickness:
       REAL*8,PARAMETER :: cLimit = 6570.0D0 ! meters
!    Changed from 5000. to 6570. on 2005.05.24, to agree with CRUST2.grd.

!   "hCMax" is an upper-limit on crustal thickness:
       REAL*8,PARAMETER :: hCMax = 75000.0D0
```

`src/OrbData5.f90:179`; nearby symbols: delta_rho_limit
```text
       REAL*8,PARAMETER :: hCMax = 75000.0D0
!    Already agreed with CRUST2.grd; no need to change!

!   "hLMax" is an upper-limit on total lithosphere thickness:
       REAL*8,PARAMETER :: hLMax = 400000.0D0
!    This limit prevents "lithosphere" from extending into the
!    transition zone, where new mineral phases appear,
!    and the input physical parameters would therefore not be valid.

```

`src/OrbData5.f90:186`; nearby symbols: delta_rho_limit
```text
!    and the input physical parameters would therefore not be valid.

!   "delta_rho_limit" is the maximum permitted size of chemical
!    density anomalies throughout the lithosphere:
       REAL*8,PARAMETER :: delta_rho_limit = 100.0D0 ! units of (kilogram per cubic meter)

!  Note that all of the above are in SI units (W/m**2, m, m, m,
!      kg/m**3, etc.)

```

`src/OrbData5.f90:192`; nearby symbols: delta_rho_limit
```text
!  Note that all of the above are in SI units (W/m**2, m, m, m,
!      kg/m**3, etc.)

!   "iUnitL" = Fortran device number for -Assign- log file:
       INTEGER,PARAMETER :: iUnitL = 13

!---------------------------------------------------------------------

!                   BEGINNING OF EXECUTABLE CODE
```

`src/OrbData5.f90:223`; nearby symbols: conduc
```text
     &//' by Peter Bird, Dept. of Earth, Planetary, & Space Sciences,' &
     & /' University of California, Los Angeles, CA 90095-1567.' &
     &//' Reads a finite element grid produced by OrbWin (or OrbWeave)' &
     & /'   (that was run in Shells-mode)' &
     & /'    and a parameter file (formatted for Shells) with' &
     & /'    thermal conductivities, densities, et cetera.' &
     & /'    Then, fills-in or computes nodal data:' &
     & /'   -elevation (+ above sea level, - below);' &
     & /'   -heat-flow;' &
```

`src/OrbData5.f90:291`; nearby symbols: TAsthK, TADIAB, GRADIE
```text
     &         /'warning messages from subprogram -Assign-:')


!   Lithosphere/asthenosphere temperature, in Kelvin, is determined
!      from the asthenosphere adiabat in the parameter file,
!      evaluated at (rather arbitrarily) 100 km depth:

       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

```

`src/OrbData5.f90:296`; nearby symbols: dQdTdA, TAsthK, TADIAB, GRADIE
```text
!      evaluated at (rather arbitrarily) 100 km depth:

       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

!   Read finite-element grid on unit 2:

       CALL GetNet (     2, iUnitVerb, &                          ! INTENT(IN)
     &               mxDOF,  mxEl,  mxFEl, mxNode, &           ! INTENT(IN)
     &               brief, &                                  ! INTENT(OUT)
```

`src/OrbData5.f90:298`; nearby symbols: dQdTdA, TAsthK, TADIAB, GRADIE
```text
       TAsthK = TAdiab + gradie * 100.0D3 ! where 100 km is expressed in meters

!   Read finite-element grid on unit 2:

       CALL GetNet (     2, iUnitVerb, &                          ! INTENT(IN)
     &               mxDOF,  mxEl,  mxFEl, mxNode, &           ! INTENT(IN)
     &               brief, &                                  ! INTENT(OUT)
     &               continuum_LRi, &                          ! INTENT(OUT)
     &               dQdTdA,   elev, &                         ! INTENT(OUT)
```

`src/OrbData5.f90:365`; nearby symbols: dQdTdA, needQ
```text
   69       FORMAT (/' All nodes have non-zero elevation.' &
     &              /' No elevation grid is needed.')
       END IF

!   Read in heat-flow array on unit 4, if needed:

       needQ = .FALSE.
       DO 70 i = 1, numNod
            IF (dQdTdA(i) == 0.0D0) needQ = .TRUE.
```

`src/OrbData5.f90:374`; nearby symbols: dQdTdA, needQ, qArray
```text
   70  CONTINUE

       IF (needQ) THEN
            IF(Verbose) WRITE(iUnitVerb, 71)
   71       FORMAT(/ /' Attempting to read gridded heat-flow:'/)
            READ (4, * ) qX1, qDX, qX2
            READ (4, * ) qY1, qDY, qY2
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
```

`src/OrbData5.f90:375`; nearby symbols: dQdTdA, needQ, qArray
```text

       IF (needQ) THEN
            IF(Verbose) WRITE(iUnitVerb, 71)
   71       FORMAT(/ /' Attempting to read gridded heat-flow:'/)
            READ (4, * ) qX1, qDX, qX2
            READ (4, * ) qY1, qDY, qY2
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
            ALLOCATE ( qArray(nQY, nQX) )
```

`src/OrbData5.f90:376`; nearby symbols: needQ, qArray
```text
       IF (needQ) THEN
            IF(Verbose) WRITE(iUnitVerb, 71)
   71       FORMAT(/ /' Attempting to read gridded heat-flow:'/)
            READ (4, * ) qX1, qDX, qX2
            READ (4, * ) qY1, qDY, qY2
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
            ALLOCATE ( qArray(nQY, nQX) )
            READ (4, * ) ((qArray(iRow, jCol), jCol = 1, nQX), iRow = 1, nQY)
```

`src/OrbData5.f90:380`; nearby symbols: qArray
```text
            READ (4, * ) qY1, qDY, qY2
            nQX = (qX2 - qX1) / qDX + 1.5D0 ! truncating to INTEGER
            nQY = (qY2 - qY1) / qDY + 1.5
            ALLOCATE ( qArray(nQY, nQX) )
            READ (4, * ) ((qArray(iRow, jCol), jCol = 1, nQX), iRow = 1, nQY)
       ELSE ! all heat-flow values at nodes are already present in .FEG file.
            IF(Verbose) WRITE(iUnitVerb, 79)
   79       FORMAT (/' All nodes have non-zero heat-flow.' &
     &              /' No heat-flow grid is needed.')
```

`src/OrbData5.f90:396`; nearby symbols: dQdTdA, qLim0, dQL_dE, qLim1
```text
            IF (dQdTdA(i) /= 0.0D0) dQdTdA(i) = MAX(dQdTdA(i), qLimit)
            dQdTdA(i) = MIN(dQdTdA(i), qLim1)
   80  CONTINUE

!      Read dataset of gridded seafloor ages, on unit 7:
!          (Note: age > 200 Ma means "unknown" or "continental".)
       IF(Verbose) WRITE(iUnitVerb, 73)
   73  FORMAT(/ /' Attempting to read gridded ages of seafloor:'/)
       READ (7, * ) aX1, aDX, aX2
```

`src/OrbData5.f90:399`; nearby symbols: dQdTdA, qLim1
```text

!      Read dataset of gridded seafloor ages, on unit 7:
!          (Note: age > 200 Ma means "unknown" or "continental".)
       IF(Verbose) WRITE(iUnitVerb, 73)
   73  FORMAT(/ /' Attempting to read gridded ages of seafloor:'/)
       READ (7, * ) aX1, aDX, aX2
       READ (7, * ) aY1, aDY, aY2
       nAX = (aX2 - aX1) / aDX + 1.5D0 ! truncating to INTEGER
       nAY = (aY2 - aY1) / aDY + 1.5D0
```

`src/OrbData5.f90:526`; nearby symbols: alphaT, conduc, delta_rho_limit
```text
     &                arcFc*(arcanaLithosphereArray(lithoRow2,lithoCol2)- &
     &                      arcanaLithosphereArray(lithoRow2,lithoCol))
                 requestedTotalLithosphere=arcTop+arcFr*(arcBot-arcTop)
            END IF
            CALL Assign (aArray,    aX1,    aDX,    aX2,    nAX,    aDY,    aY2,    nAY, & ! INTENT(IN)
     &                   alphaT, cLimit, conduc, &                                         ! INTENT(IN)
     &                   cArray,    cX1,    cDX,    cX2,    nCX,    cDY,    cY2,    nCY, & ! INTENT(IN)
     &                   delta_rho_limit, &                                                ! INTENT(IN)
     &                   eArray,    eX1,    eDX,    eX2,    nEX,    eDY,    eY2,    nEY, & ! INTENT(IN)
```

`src/OrbData5.f90:565`; nearby symbols: dQdTdA
```text
  700  FORMAT (/ /' CHECK THE LOG FILE CAREFULLY FOR PROBLEMS!')

!   OUTPUT THE MODIFIED .FEG FILE:

       call PutNet (   14, &                                   ! INTENT(IN)
     &              brief, &                                   ! INTENT(IN)
     &              continuum_LRi, &                           ! INTENT(IN)
     &              dQdTdA,   elev, &                          ! INTENT(IN)
     &              fault_LRi, fDip, &                         ! INTENT(IN)
```

`src/OrbScore2.f90:203`; nearby symbols: dQdTdA
```text
!---------------------------------------------------------------------

!                        DIMENSION STATMENTS

!  DIMENSIONs using PARAMETER maxNod:
       LOGICAL :: checkN
       REAL*8  :: atnode, cooling_curvature, density_anomaly, dQdTdA, eDotNC, eDotNM, elev, &
                & tLNode, uvecN, xNode, yNode, zMNode
       DIMENSION atnode (maxNod), checkN (maxNod), &
```

`src/OrbScore2.f90:708`; nearby symbols: dQdTdA
```text
       LR_set_eCreep = 0.0D0
! ---------------------------------------------------------------------

!   Input finite element grid and data values at node points:
       CALL GetNet (iUnitG, iUnitVerb, &            ! input
     &              mxDOF, mxEl, mxFEl, mxNode, &
     &              brief, continuum_LRi, cooling_curvature, &  ! output
     &              density_anomaly, &
     &              dQdTdA, elev, fault_LRi, fDip, &
```

`src/OrbScore2.f90:1056`; nearby symbols: dQdTdA, alphaT, conduc
```text
            zTranF(2, i) = MAX(tLNode(nodeF(1, i)) / 2.0D0, oneKm)
       END DO
!      Then search for actual brittle/ductile transition, iteratively:
       DO iMohr = 1, 3
           CALL Mohr (alphaT, conduc, constr, &                     ! input
         &            continuum_LRi, &
         &            dQdTdA, elev, &
         &            fault_LRi, fDip, fMuMax, &
         &            fPFlt, fArg, gMean, &
```

`src/SHELLS_v5.0.f90:464`; nearby symbols: dQdTdA
```text
       LR_set_dCreep = 0.0D0
       LR_set_eCreep = 0.0D0

!   Input finite element grid and nodal data (up to 6 fields):
       CALL GetNet (iUnitG, iUnitLog, &            ! input
     &              mxDOF, mxEl, mxFEl, mxNode, &
     &              brief, continuum_LRi, cooling_curvature, &  ! output
     &              density_anomaly, &
     &              dQdTdA, elev, fault_LRi, fDip, &
```

`src/SHELLS_v5.0.f90:473`; nearby symbols: dQdTdA
```text
     &              nFakeN, nFl, nodeF, nodes, nRealN, &
     &              numEl, numNod, n1000, offMax, offset, &
     &              title1, tLNode, xNode, yNode, zMNode, &
     &              checkE, checkF, checkN)      ! work
       IF(Verbose) WRITE(iUnitVerb, "(' Finite element grid file has been read.')")

      !Remember the default ("d_") Lithospheric Rheology as LR0, or LR_set_XXXX(0):
       LR_set_fFric(0)       = fFric
       LR_set_cFric(0)       = cFric
```

`src/SHELLS_v5.0.f90:675`; nearby symbols: dQdTdA, alphaT, conduc, GRADIE
```text

!   Interpolate and initialize all "convenience arrays":

       IF(Verbose) WRITE(iUnitVerb, "(/' Constant arrays are being computed.')")
       CALL FillIn (alphaT, basal, conduc, &                  ! input
     &              continuum_LRi, &
     &              cooling_curvature, &
     &              density_anomaly, &
     &              dQdTdA, elev, &
```

`src/SHELLS_v5.0.f90:711`; nearby symbols: dQdTdA, alphaT, conduc
```text
       doFB1 = .TRUE.
       doFB2 = .TRUE.
       doFB3 = .TRUE.
       doFB4 = .TRUE.
       CALL Fixed (alphaT, area, conduc, &   ! input
     &             density_anomaly, detJ, &
     &             doFB1, doFB2, doFB3, doFB4, &
     &             dQdTdA, dXS, dYS, &
     &             dXSP, dYSP, edgeTS, elev, fDip, fLen, fPFlt, &
```

`src/SHELLS_v5.0.f90:731`; nearby symbols: dQdTdA, alphaT, conduc
```text
!      horizontal velocity components (using iteration to handle
!      nonlinearities):

       IF(Verbose) WRITE(iUnitVerb, "(/' Beginning the iterative solution for velocity.')")
       CALL Pure (alphaT, area, &                               ! input
     &            basal, &
     &            conduc, constr, continuum_LRi, &
     &            delta_rho, detJ, dQdTdA, dXS, dYS, &
     &            elev, etaMax, everyP, &
```

`src/SHELLS_v5.0.f90:757`; nearby symbols: dQdTdA, alphaT, conduc
```text
     &            alpha, dv, dVLast, force, fC, fTStar, &       ! work
     &            outVec, stiff, ipiv, tOfset, ThID, SHELLSconv)
!   Test and display the equilibrium found:

       CALL Balanc (alphaT, area, conduc, constr, &        ! input
     &              density_anomaly, detJ, dQdTdA, dXS, &
     &              dXSP, dYS, dYSP, edgeTS, elev, eta, &
     &              fArg, fC, fDip, &
     &              fIMuDZ, fLen, fPFlt, fPSfer, fTStar, &
```

`src/SHELLS_v5.0.f90:779`; nearby symbols: alphaT
```text
     &              fBase, outVec)                        ! work

!   Output the solution:

       CALL Result (alphaT, area, comp, detJ, elev, eRate, everyP, & ! input
     &              fault_LRi, &
     &              fDip, fIMuDZ, fPFlt, fPeakS, fPSfer, fSlips, &
     &              fArg, geothC, iUnitQ, iUnitS, iUnitLog, &
     &              log_node_velocities, &
```

`src/ShellSetMain.f90:577`; nearby symbols: alphaT, conduc
```text
    end if

    ModNum = msg_stat(MPI_TAG)

    call readDATA(DataFiles)
    write(filename,'(2A)') "INPUT/"//trim(DataFiles(2))

    open(unit=1,file=trim(filename))
    call ReadPm (     1, iUnitVerb, names,  nPlate, offMax, & ! INTENT(IN)
```

`src/ShellSetMain.f90:580`; nearby symbols: alphaT, conduc, GRADIE
```text

    call readDATA(DataFiles)
    write(filename,'(2A)') "INPUT/"//trim(DataFiles(2))

    open(unit=1,file=trim(filename))
    call ReadPm (     1, iUnitVerb, names,  nPlate, offMax, & ! INTENT(IN)
      &          aCreep, alphaT,    bCreep, Biot  , Byerly, & ! INTENT(OUT)
      &          cCreep, cFric,     conduc, dCreep, eCreep, &
      &          everyP, fFric,     gMean , gradie, iConve, &
```

`src/ShellSetMain.f90:581`; nearby symbols: alphaT, conduc, temLim, TADIAB, GRADIE
```text
    call readDATA(DataFiles)
    write(filename,'(2A)') "INPUT/"//trim(DataFiles(2))

    open(unit=1,file=trim(filename))
    call ReadPm (     1, iUnitVerb, names,  nPlate, offMax, & ! INTENT(IN)
      &          aCreep, alphaT,    bCreep, Biot  , Byerly, & ! INTENT(OUT)
      &          cCreep, cFric,     conduc, dCreep, eCreep, &
      &          everyP, fFric,     gMean , gradie, iConve, &
      &          iPVRef, maxItr,    OKDelV, OKToQt, oneKm,  &
```

`src/ShellSetMain.f90:602`; nearby symbols: TADIAB
```text
      call MPI_Abort(MPI_COMM_WORLD,10)
    elseif(MaxIter == 0 .and. (iConve == 0 .or. iConve == 6)) then
      write(ErrorMsg,'(A,I0,A)') "The iConve value ",iConve," expects -Iter to be >0"
      call FatalError(ErrorMsg,ModNum)
      call abort(10)
      if(FileExist('FatalError.txt')) call execute_command_line('rm FatalError.txt')
      call MPI_Abort(MPI_COMM_WORLD,10)
    end if

```

`src/ShellSetMain.f90:603`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
    elseif(MaxIter == 0 .and. (iConve == 0 .or. iConve == 6)) then
      write(ErrorMsg,'(A,I0,A)') "The iConve value ",iConve," expects -Iter to be >0"
      call FatalError(ErrorMsg,ModNum)
      call abort(10)
      if(FileExist('FatalError.txt')) call execute_command_line('rm FatalError.txt')
      call MPI_Abort(MPI_COMM_WORLD,10)
    end if

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
```

`src/ShellSetMain.f90:604`; nearby symbols: TADIAB, GRADIE, ZBASTH
```text
      write(ErrorMsg,'(A,I0,A)') "The iConve value ",iConve," expects -Iter to be >0"
      call FatalError(ErrorMsg,ModNum)
      call abort(10)
      if(FileExist('FatalError.txt')) call execute_command_line('rm FatalError.txt')
      call MPI_Abort(MPI_COMM_WORLD,10)
    end if

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
```

`src/ShellSetMain.f90:607`; nearby symbols: alphaT, conduc, TSurf, temLim, TADIAB, GRADIE, ZBASTH
```text
      if(FileExist('FatalError.txt')) call execute_command_line('rm FatalError.txt')
      call MPI_Abort(MPI_COMM_WORLD,10)
    end if

    call Variable_Update( fFric, cFric,  Biot,   Byerly, aCreep, &
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
```

`src/ShellSetMain.f90:612`; nearby symbols: alphaT, conduc, TSurf, temLim, TADIAB, GRADIE, ZBASTH
```text
      &                  bCreep, cCreep, dCreep, eCreep, tAdiab, &
      &                  gradie, zBAsth, trHMax, tauMax, rhoH2O, &
      &                  rhoBar, rhoAst, gMean,  oneKm,  radius, &
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
    if(Verbose) then
      write(iUnitVerb,"(/A)")"The following variables were updated before being used by any of OrbData, Shells or OrbScore"
      write(frmt,"(A,I0,A)") "(",size(ListVarNames),"(A,X),/)"
      write(iUnitVerb,frmt), (trim(ListVarNames(i)), i =1,size(ListVarNames))
```

`src/ShellSetMain.f90:615`; nearby symbols: alphaT, conduc, TSurf, temLim, GRADIE, ZBASTH
```text
      &                  alphaT, conduc, radio,  tSurf,  temLim, &
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
    if(Verbose) then
      write(iUnitVerb,"(/A)")"The following variables were updated before being used by any of OrbData, Shells or OrbScore"
      write(frmt,"(A,I0,A)") "(",size(ListVarNames),"(A,X),/)"
      write(iUnitVerb,frmt), (trim(ListVarNames(i)), i =1,size(ListVarNames))

      write(iUnitVerb,"(A)") "With the following values:"
      call FormatStrings('MisL',ListVarNames,0,frmt)
```

`src/ShellSetMain.f90:616`; nearby symbols: alphaT, conduc, TSurf, temLim
```text
      &                  ListVarNames, ListVarValues(1,:)) ! ListVarValues(1,:) because only relevant values sent to worker
    if(Verbose) then
      write(iUnitVerb,"(/A)")"The following variables were updated before being used by any of OrbData, Shells or OrbScore"
      write(frmt,"(A,I0,A)") "(",size(ListVarNames),"(A,X),/)"
      write(iUnitVerb,frmt), (trim(ListVarNames(i)), i =1,size(ListVarNames))

      write(iUnitVerb,"(A)") "With the following values:"
      call FormatStrings('MisL',ListVarNames,0,frmt)
      write(iUnitVerb,frmt), (ListVarValues(1,i), i =1,size(ListVarValues,2)),' '
```

`src/ShellSetMain.f90:771`; nearby symbols: alphaT, conduc, TSurf, temLim, TADIAB, GRADIE, ZBASTH
```text

! Update variables between 1st & 2nd iteration?
        if(rpeat==1 .and. FileExist('INPUT/UpVar.in')) then
          if(ThID==1 .and. Verbose) write(iUnitVerb,'(A)') 'UpVar.in file detected, updating listed variables'
          call IterVar(fFric, cFric,  Biot,   Byerly, aCreep, &
          &           bCreep, cCreep, dCreep, eCreep, tAdiab, &
          &           gradie, zBAsth, trHMax, tauMax, rhoH2O, &
          &           rhoBar, rhoAst, gMean,  oneKm,  radius, &
          &           alphaT, conduc, radio,  tSurf,  temLim)
```

`src/ShellSetMain.f90:781`; nearby symbols: alphaT, conduc, TSurf, temLim
```text


      end do ! do while(rpeat<MaxIter .and. SHELLSconv)

! Final or non-iterating Shells call
      if(SHELLSconv) then ! Final call with (optional) different files
        if(MaxIter /= 0) rpeat = rpeat+1 ! necessary since rpeat updated at beginning of main loop
        call OpenInput(ThID,ModNum,"SF",DirName,rpeat=rpeat)
        call OpenOutput(ThID,ModNum,"SF",DirName,rpeat=rpeat)
```

## Interpretation status

Excerpts must be adjudicated against call order, parameter binding and active runtime path. Automated matches do not establish scientific semantics.

Preserved gates: `PRE_ORBDATA_ready=false`; `t0_orbdata_executed=false`; `shellset_mechanics_authorized=false`; `dt_selected=false`; `t1_created=false`; `forward_evolution_authorized=false`.
