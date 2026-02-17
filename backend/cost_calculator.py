from financial_engine import calculate_loan_payment

def _get_mileage_and_efficiency(car_row, inputs):
    # annual mileage city/hwy split
    if 'commute_dist' in inputs:
        commute_daily_rt = inputs.get('commute_dist', 20)
        days_week = inputs.get('days_week', 5)
        road_trip_annual = inputs.get('road_trip_miles', 1000)
        other_weekly = inputs.get('other_miles', 50)
        commute_type = inputs.get('commute_type', 'Mixed')
        
        commute_annual = commute_daily_rt * days_week * 50
        other_annual = other_weekly * 52
        annual_miles = commute_annual + road_trip_annual + other_annual
        
        # ratio
        commute_hwy_pct = 0.45 
        if commute_type == "Mostly Highway": commute_hwy_pct = 0.85
        elif commute_type == "Mostly City": commute_hwy_pct = 0.15
        
        hwy_miles = (road_trip_annual * 1.0) + (commute_annual * commute_hwy_pct) + (other_annual * 0.2)
        pct_hwy = hwy_miles / annual_miles if annual_miles > 0 else 0.5
        pct_city = 1.0 - pct_hwy
        
        # weighted mpg
        avg_mpg = (car_row.get('city_mpg', 25) * pct_city) + (car_row.get('hwy_mpg', 30) * pct_hwy)
    else:
        # fallback
        annual_miles = inputs.get('annual_miles', 12000)
        avg_mpg = (car_row.get('city_mpg', 25) * 0.55) + (car_row.get('hwy_mpg', 30) * 0.45)

    # environment
    climate = inputs.get('climate', 'Moderate')
    terrain = inputs.get('terrain', 'Flat')
    eff_modifier = 1.0
    
    # ev owners be like (me)
    is_electric = car_row.get('fuel_type') == 'Electric'
    if climate == 'Cold (Winter)':
        eff_modifier *= 0.75 if is_electric else 0.85
    elif climate == 'Hot (Summer)':
        eff_modifier *= 0.85 if is_electric else 0.90
    
    # terrain
    if terrain == 'Hilly': eff_modifier *= 0.90
    elif terrain == 'Mountainous': eff_modifier *= 0.80
        
    adj_mpg = avg_mpg * eff_modifier

    
    return annual_miles, adj_mpg, eff_modifier

def _calculate_operational_costs(car_row, inputs, annual_miles, adj_mpg, eff_modifier):
    gas_price = inputs.get('gas_price', 3.50)
    elec_price = inputs.get('elec_price', 0.16)
    elec_price_road = inputs.get('elec_price_road', 0.36)

    if car_row.get('fuel_type') == 'Electric':
        # epa calculation mpge to mpkwh even tho highly dependent
        miles_per_kwh = adj_mpg / 33.7
        
        # road vs home charging cost
        fast_charge_miles = inputs.get('road_trip_miles', 0)
        range_est = car_row.get('range_miles', 250) * eff_modifier
        daily_commute = inputs.get('commute_dist', 20)
        
        # overflow miles using road charging cost
        # TODO: work charging
        if daily_commute > range_est:
            overflow_per_day = daily_commute - range_est
            days_driven = inputs.get('days_week', 5) * 50
            fast_charge_miles += (overflow_per_day * days_driven)
        
        home_charge_miles = max(0, annual_miles - fast_charge_miles)
        
        cost_home = (home_charge_miles / miles_per_kwh) * elec_price
        cost_fast = (fast_charge_miles / miles_per_kwh) * elec_price_road
        monthly_fuel = (cost_home + cost_fast) / 12
    else:
        # gas/hybird mpg for now
        monthly_fuel = ((annual_miles / 12) / adj_mpg) * gas_price

    # maintenance for reliability + luxury
    base_maint_rate = 0.09
    rel_score = car_row.get('reliability_score', 5)
    lux_score = car_row.get('luxury_score', 5)
    
    rel_multiplier = 2.0 - ((rel_score - 1) * (1.2 / 9))
    # idk lol
    lux_multiplier = 1.0 + (lux_score * 0.05)
    monthly_maint = ((annual_miles / 12) * base_maint_rate * rel_multiplier * lux_multiplier)

    # age scaled insurance rates
    custom_ins = inputs.get('custom_insurance', 0)
    if custom_ins > 0:
        monthly_ins = custom_ins
    else:
        base_ins = (1200 + (car_row.get('price', 30000) * 0.015)) / 12
        driver_age = inputs.get('driver_age', 30)
        
        age_factor = 1.0
        if driver_age < 18: age_factor = 1.8
        elif driver_age < 21: age_factor = 1.5
        elif driver_age < 25: age_factor = 1.3
        elif driver_age > 70: age_factor = 1.2
        
        monthly_ins = base_ins * age_factor

    return monthly_fuel, monthly_maint, monthly_ins

def _calculate_financials(car_row, inputs, years, resale_model):
    buying_method = inputs.get('method', 'Cash')
    price = car_row.get('price', 30000)
    
    monthly_payment = 0.0
    upfront_cost = 0.0
    future_value = 0.0
    monthly_depreciation = 0.0

    def predict_value():
        if resale_model:
            try:
                return resale_model.predict_future_value(car_row, years)
            except:
                pass
        # Fallback
        dep_modifier = 1.2 if car_row.get('luxury_score', 5) > 7 else 1.0
        return price * ((1 - (0.12 * dep_modifier)) ** years)

    if buying_method == 'Cash':
        future_value = predict_value()
        total_depreciation = price - future_value
        monthly_depreciation = total_depreciation / (years * 12)
        upfront_cost = price
        
    elif buying_method == 'Finance':
        apr = inputs.get('apr', 6.0)
        term = inputs.get('term', 60)
        down_payment = inputs.get('down_payment', 0)
        
        loan_amount = price - down_payment
        monthly_payment = calculate_loan_payment(loan_amount, apr, term)
        upfront_cost = down_payment
        
        future_value = predict_value()
        total_depreciation = price - future_value
        monthly_depreciation = total_depreciation / (years * 12)

    elif buying_method == 'Lease':
        user_monthly = inputs.get('lease_monthly', 0)
        user_due = inputs.get('lease_due', 0)
        user_term = inputs.get('lease_term', 36)
        
        if user_monthly > 0:
            monthly_payment = user_monthly
            upfront_cost = user_due
            # lease specific value for deprication var
            monthly_depreciation = (user_due / user_term) if user_term > 0 else 0
        else:
            monthly_payment = price * 0.012 
            upfront_cost = 2000 
        
        future_value = 0 # lease sepecific calulator

    return monthly_payment, monthly_depreciation, upfront_cost, future_value

def calculate_tco(car_row, inputs, resale_model=None):
    years = inputs.get('years', 5)
    
    # mileage
    annual_miles, adj_mpg, eff_modifier = _get_mileage_and_efficiency(car_row, inputs)
    
    # operation cost
    m_fuel, m_maint, m_ins = _calculate_operational_costs(car_row, inputs, annual_miles, adj_mpg, eff_modifier)
    
    # asset cost
    m_pmt, m_dep, upfront, future_val = _calculate_financials(car_row, inputs, years, resale_model)

    # add
    m_ops = m_fuel + m_maint + m_ins
    m_cash_flow = m_ops + m_pmt
    
    buying_method = inputs.get('method', 'Cash')
    
    if buying_method == 'Finance':
        # TCO = Ops + Dep + Interest (simplified approximation via payment diff)
        # Interest paid ≈ (Total Payments + Down) - Price
        term = inputs.get('term', 60)
        total_paid_loan = (m_pmt * term) + inputs.get('down_payment', 0)
        total_interest = total_paid_loan - car_row.get('price', 30000)
        avg_monthly_interest = total_interest / term if term > 0 else 0
        m_tco = m_ops + m_dep + avg_monthly_interest
        
    elif buying_method == 'Lease':
        # TCO = Ops + Lease Payment + Amortized Down
        lease_term = inputs.get('lease_term', 36)
        amortized_down = (upfront / lease_term) if lease_term > 0 else 0
        m_tco = m_ops + m_pmt + amortized_down
        
    else: # Cash
        # TCO = Ops + Depreciation (Loss of asset value)
        m_tco = m_ops + m_dep

    return {
        'buying_method': buying_method,
        'Monthly Payment': round(m_pmt, 2),
        'Monthly Fuel': round(m_fuel, 2),
        'Monthly Maint': round(m_maint, 2),
        'Monthly Ins': round(m_ins, 2),
        'Monthly Dep': round(m_dep, 2),
        'Upfront Cost': round(upfront, 2),
        'Monthly Cash Flow': round(m_cash_flow, 2), 
        'Monthly True Cost': round(m_tco, 2), 
        'Total 5yr Cost': round(m_tco * 60, 2),
        'Calculated Annual Miles': round(annual_miles, 0),
        'Est MPG': round(adj_mpg, 1),
        'Resale Value': round(future_val, 0)
    }