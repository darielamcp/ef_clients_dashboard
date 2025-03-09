fp_resolution_org_s = {'outbound': 'STATE', 'intrastate': 'STATE', 'inbound': 'COUNTRY'}
fp_resolution_dest_s = {'outbound': 'COUNTRY', 'intrastate': 'STATE', 'inbound': 'STATE'}
fp_resolution_org_h = {'outbound': 'HUB', 'intrastate': 'HUB', 'inbound': 'COUNTRY'}
fp_resolution_dest_h = {'outbound': 'COUNTRY', 'intrastate': 'HUB', 'inbound': 'HUB'}
fp_col_loc = {'outbound': 'origin', 'intrastate': 'origin', 'inbound': 'destination'}
fp_col_value = {'income': 'income', 'profit': 'profit', 'cost': 'cost'}
fp_agg_type = {'total': '', 'per day': 'days', 'per mile': 'distance'}
fp_frequency = {'total': 'Y', 'annual': 'Y', 'quarterly': 'Q', 'monthly': 'M', 'weekly':'W', 'daily': 'D'}
fp_coords = {'origin': ['lat_org', 'lng_org'], 'destination': ['lat_dest', 'lng_dest']}
bs_type_broker = {'Good negotiation strength':'good', 'Potential':'potential', 'Weak negotiation strength':'bad'}
bs_col_value = {'income_perday': 'income_day', 'income_permile': 'income_dist', 'profit_perday': 'profit_day', 'profit_permile': 'profit_dist', 'cost_perday': 'cost_day', 'cost_permile': 'cost_dist',
                'income_total': 'income', 'profit_total': 'profit', 'cost_total': 'cost'}
back_cols = {'inbound':('state_destination', 'destination', 'origin'), 'outbound':('state_origin', 'origin', 'destination')}
