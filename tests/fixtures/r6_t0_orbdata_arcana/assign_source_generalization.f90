! Synthetic unit fixture for the FAIR ShellSet source patch. Constants here are
! test parameters only and are not ARCANA T0 model configuration.
program assign_source_generalization
  use DATA_subs, only: Assign
  use SharedVars, only: ThID, Verbose
  use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
  implicit none
  integer :: modnum, domain_class, domain_row, domain_col
  real*8 :: age(2,2), crust(2,2), elevation_grid(2,2), q_grid(2,2), s_grid(2,2)
  real*8 :: alpha(2), conductivity(2), radioactivity(2), density_bar(2), temp_limit(2)
  real*8 :: delta_rho_limit, gmean, hCmax, hLmax, oneKm, pLon, pLat
  real*8 :: qLim0, dQLdE, qLim1, rhoAst, rhoH2O, TAsthK, TSurf
  real*8 :: elevation, heat_flow, thickC, thickM, chemical_delta_rho, cooling_curvature
  real*8 :: result_low_s, result_high_s, result_stock_low_s, result_stock_high_s
  real*8 :: requested_total
  real*8 :: domain_grid(2,2), expected_mantle_initial, continental_final, ocean_final
  logical :: arcana_mode, arcana_ocean
  integer :: i

  modnum=1
  ThID=1
  Verbose=.false.
  alpha=(/3.0D-5,3.0D-5/)
  conductivity=(/2.5D0,3.0D0/)
  radioactivity=(/1.0D-6,1.0D-6/)
  density_bar=(/2800.0D0,3300.0D0/)
  temp_limit=(/1600.0D0,1600.0D0/)
  delta_rho_limit=300.0D0
  gmean=9.8D0
  hCmax=60000.0D0
  hLmax=300000.0D0
  oneKm=1000.0D0
  pLon=-0.5D0
  pLat=-0.5D0
  qLim0=0.005D0
  dQLdE=0.0D0
  qLim1=0.12D0
  rhoAst=3300.0D0
  rhoH2O=1000.0D0
  TAsthK=1600.0D0
  TSurf=273.0D0
  crust=35000.0D0
  elevation_grid=-5000.0D0
  q_grid=0.05D0
  age=20.0D0
  s_grid=0.0D0
  requested_total=135000.0D0
  elevation=0.0D0
  heat_flow=0.05D0

  ! Synthetic coast cell: a low interpolated age suggests ocean to stock mode,
  ! while the categorical ARCANA fixture cell identifies a continent.
  domain_grid=2.0D0
  domain_row=INT((0.0D0-pLat)/1.0D0+1.50000001D0)
  domain_col=INT((pLon-(-1.0D0))/1.0D0+1.50000001D0)
  domain_class=NINT(domain_grid(domain_row,domain_col))
  arcana_ocean=(domain_class==1)
  arcana_mode=.true.
  call AssignFixture(age,crust,elevation_grid,q_grid,s_grid,arcana_mode,arcana_ocean,requested_total, &
       elevation,heat_flow,thickC,thickM,chemical_delta_rho,cooling_curvature)
  result_low_s=thickM
  continental_final=thickM
  expected_mantle_initial=requested_total-thickC
  if (elevation/=0.0D0) error stop "explicit mode changed valid zero elevation"
  if (.not. ieee_is_finite(chemical_delta_rho) .or. .not. ieee_is_finite(cooling_curvature)) &
       error stop "downstream Assign outputs were not finite"
  if (thickM<0.0D0 .or. thickM>hLmax-thickC) error stop "explicit mantle thickness outside source bounds"

  ! An extreme synthetic S-wave array must not affect explicit continental mode.
  s_grid=1.0D12
  call AssignFixture(age,crust,elevation_grid,q_grid,s_grid,arcana_mode,arcana_ocean,requested_total, &
       elevation,heat_flow,thickC,thickM,chemical_delta_rho,cooling_curvature)
  result_high_s=thickM
  if (abs(result_high_s-result_low_s)>1.0D-8) error stop "explicit mode consumed sArray"

  ! Without the input pair, the source S-wave branch remains active.
  age=250.0D0
  arcana_mode=.false.
  arcana_ocean=.false.
  s_grid=0.0D0
  call AssignFixture(age,crust,elevation_grid,q_grid,s_grid,arcana_mode,arcana_ocean,requested_total, &
       elevation,heat_flow,thickC,result_stock_low_s,chemical_delta_rho,cooling_curvature)
  s_grid=1.0D12
  call AssignFixture(age,crust,elevation_grid,q_grid,s_grid,arcana_mode,arcana_ocean,requested_total, &
       elevation,heat_flow,thickC,result_stock_high_s,chemical_delta_rho,cooling_curvature)
  if (abs(result_stock_high_s-result_stock_low_s)<1.0D-6) error stop "stock mode did not consume sArray"

  ! Domain 1 selects age physics even with an old-age value (>200 Ma), proving
  ! that domain selection is independent of age interpolation.
  age=250.0D0
  domain_grid(domain_row,domain_col)=1.0D0
  domain_class=NINT(domain_grid(domain_row,domain_col))
  arcana_mode=.true.
  arcana_ocean=(domain_class==1)
  s_grid=1.0D12
  call AssignFixture(age,crust,elevation_grid,q_grid,s_grid,arcana_mode,arcana_ocean,requested_total, &
       elevation,heat_flow,thickC,thickM,chemical_delta_rho,cooling_curvature)
  if (.not. ieee_is_finite(thickM) .or. thickM<=0.0D0) error stop "explicit ocean age branch failed"
  ocean_final=thickM

  print '(A,ES16.8)', "REQUESTED_TOTAL_LITHOSPHERE_M=",requested_total
  print '(A,ES16.8)', "EXPECTED_INITIAL_MANTLE_COMPONENT_M=",expected_mantle_initial
  print '(A,ES16.8)', "FINAL_CONTINENTAL_MANTLE_COMPONENT_M=",continental_final
  print '(A,ES16.8)', "FINAL_OCEANIC_MANTLE_COMPONENT_M=",ocean_final
  print '(A,ES16.8)', "STOCK_SARRAY_DELTA_M=",result_stock_high_s-result_stock_low_s
  print '(A)', "ARCANA_SYNTHETIC_ASSIGN_FIXTURE=PASS"

contains

  subroutine AssignFixture(a,c,e,q,s,mode,ocean,total,elev,heat,tc,tm,chem,cool)
    real*8, intent(in) :: a(2,2),c(2,2),e(2,2),q(2,2),s(2,2),total
    logical, intent(in) :: mode,ocean
    real*8, intent(inout) :: elev,heat
    real*8, intent(out) :: tc,tm,chem,cool
    call Assign(a,-1.0D0,1.0D0,0.0D0,2,1.0D0,0.0D0,2, &
         alpha,0.0D0,conductivity,c,-1.0D0,1.0D0,0.0D0,2,1.0D0,0.0D0,2, &
         delta_rho_limit,e,-1.0D0,1.0D0,0.0D0,2,1.0D0,0.0D0,2, &
         gmean,hCmax,hLmax,6,6,oneKm,pLon,pLat,qLim0,dQLdE,qLim1, &
         q,-1.0D0,1.0D0,0.0D0,2,1.0D0,0.0D0,2, &
         radioactivity,rhoAst,density_bar,rhoH2O, &
         s,-1.0D0,1.0D0,0.0D0,2,1.0D0,0.0D0,2, &
         TAsthK,temp_limit,TSurf,elev,heat,tc,tm,chem,cool,mode,ocean,total,modnum)
  end subroutine AssignFixture
end program assign_source_generalization
