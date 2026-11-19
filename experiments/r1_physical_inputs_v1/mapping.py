"""Read-only preparation: area-overlap remap with explicit UNKNOWN support.

No R1 imports or physical time advance. A mapped elevation is NOT mobile cover.
"""
import numpy as np

def remap(values,known,source_lat,source_lon,target_lat,target_lon,radius):
    v=np.asarray(values);known=np.asarray(known,dtype=bool)
    if v.shape!=known.shape or v.ndim!=2:raise ValueError('SHAPE')
    if not np.isfinite(v[known]).all():raise ValueError('KNOWN_NONFINITE')
    if radius<=0 or not np.isfinite(radius):raise ValueError('RADIUS')
    sl=np.sin(np.deg2rad(np.asarray(source_lat,dtype=np.longdouble)));tl=np.sin(np.deg2rad(np.asarray(target_lat,dtype=np.longdouble)))
    so=np.deg2rad(np.asarray(source_lon,dtype=np.longdouble));to=np.deg2rad(np.asarray(target_lon,dtype=np.longdouble))
    for x in [sl,tl,so,to]:
        if not np.all(np.diff(x)>0):raise ValueError('NONMONOTONE_EDGES')
    if v.shape!=(len(sl)-1,len(so)-1):raise ValueError('GRID_SHAPE')
    if not (sl[0]==tl[0] and sl[-1]==tl[-1] and so[0]==to[0] and so[-1]==to[-1]):raise ValueError('EXTENT')
    lat=np.maximum(0,np.minimum(tl[1:,None],sl[None,1:])-np.maximum(tl[:-1,None],sl[None,:-1]))
    lon=np.maximum(0,np.minimum(to[1:,None],so[None,1:])-np.maximum(to[:-1,None],so[None,:-1]))
    area=np.longdouble(radius)**2*np.diff(tl)[:,None]*np.diff(to)[None,:]
    # Zero is only an integration filler multiplied by explicit support, never an imputed field value.
    weighted=np.where(known,v,0).astype(np.longdouble)
    known_area=np.longdouble(radius)**2*(lat@known.astype(np.longdouble)@lon.T)
    integral=np.longdouble(radius)**2*(lat@weighted@lon.T)
    intersects_unknown=((lat>0).astype('i4')@(~known).astype('i4')@(lon>0).astype('i4').T)>0
    supported=np.divide(integral,known_area,out=np.full_like(integral,np.nan),where=known_area>0)
    full_mean=supported.copy();full_mean[intersects_unknown]=np.nan
    src_area=np.longdouble(radius)**2*np.diff(sl)[:,None]*np.diff(so)[None,:]
    src_sum=np.sum(src_area*weighted);dst_sum=np.sum(integral)
    scale=max(np.longdouble(1),np.sum(src_area*np.abs(weighted)))
    return {'full_cell_mean':np.asarray(full_mean,dtype=float),'mean_over_known_subarea':np.asarray(supported,dtype=float),
      'known_area_m2':np.asarray(known_area,dtype=float),'target_area_m2':np.asarray(area,dtype=float),
      'known_fraction':np.asarray(known_area/area,dtype=float),'has_UNKNOWN':intersects_unknown,
      'known_integral_value_m2':np.asarray(integral,dtype=float),
      'relative_discrete_integral_residual':float((dst_sum-src_sum)/scale),
      'source_known_area_m2':float(np.sum(src_area*known)),'target_known_area_m2':float(np.sum(known_area)),
      'source_known_integral':float(src_sum),'target_known_integral':float(dst_sum)}

def admit_cover(quantity,units,kappa,kappa_units,known,law_binding,parameter_origin):
    reasons=[]
    if quantity!='mobile_cover_thickness':reasons.append('FIELD_IS_NOT_MOBILE_COVER_THICKNESS')
    if units!='m':reasons.append('THICKNESS_UNIT_NOT_METRES')
    if kappa is None:reasons.append('PHYSICAL_SURFACE_DIFFUSIVITY_MISSING')
    elif not np.isfinite(kappa) or kappa<0:reasons.append('PHYSICAL_DIFFUSIVITY_INVALID')
    if kappa_units!='m2/model_year':reasons.append('SURFACE_DIFFUSIVITY_UNITS_UNBOUND')
    if not np.asarray(known,dtype=bool).all():reasons.append('GLOBAL_R1_STENCIL_INTERSECTS_UNKNOWN')
    if law_binding!='dh_dt=kappa*Laplace_Beltrami(h);constant_kappa;declared_substrate_boundary':reasons.append('PHYSICAL_LAW_SUBSTRATE_BOUNDARY_UNBOUND')
    if parameter_origin in [None,'synthetic_test','thermal_conductivity']:reasons.append('PARAMETER_NOT_PHYSICAL_SURFACE_DIFFUSIVITY')
    return {'admitted':not reasons,'reasons':reasons,'density_required_for_volume_only':False,'density_required_for_mass':True}

def unit_checks():
    sl=np.linspace(-90,90,5);so=np.linspace(-180,180,9);tl=np.linspace(-90,90,3);to=np.linspace(-180,180,5)
    values=np.arange(32,dtype=float).reshape(4,8)+1;known=np.ones_like(values,dtype=bool)
    first=remap(values,known,sl,so,tl,to,6371000.)
    assert abs(first['relative_discrete_integral_residual'])<2e-14 and not first['has_UNKNOWN'].any()
    known[0,0]=False;values[0,0]=np.nan;second=remap(values,known,sl,so,tl,to,6371000.)
    assert second['has_UNKNOWN'][0,0] and np.isnan(second['full_cell_mean'][0,0]) and np.isfinite(second['mean_over_known_subarea'][0,0])
    assert abs(second['relative_discrete_integral_residual'])<2e-14
    empty=remap(values,np.zeros_like(known),sl,so,tl,to,6371000.)
    assert np.isnan(empty['full_cell_mean']).all() and (empty['known_fraction']==0).all()
    return {'synthetic_adapter_only':True,'area_integral':'PASS','unknown_not_filled':'PASS','empty_support':'PASS','solver_calls':0}
