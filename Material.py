class XPF():
    '''Material Class for Expanded Polystyrene'''
    def __init__(self):
        self.thermal_conductivity =
        self.specific_heat_capacity =
        self.density =
        self.thermal_diffusivity = self.thermal_conductivity/(self.specific_heat_capacity*self.density)

class EPP():
    '''Material Class for Expanded Polypropolene'''
    def __init__(self):
        self.thermal_conductivity = 0.035
        self.specific_heat_capacity = 1300
        self.density = 52.3
        self.thermal_diffusivity = self.thermal_conductivity/(self.specific_heat_capacity*self.density)


class EPE():
    '''Material Class for Expanded Polyethelene'''
    def __init__(self):
        self.thermal_conductivity = 0.034
        self.specific_heat_capacity = 1300
        self.density = 52.3
        self.thermal_diffusivity = self.thermal_conductivity/(self.specific_heat_capacity*self.density)

class EPS():
    '''Material Class for Expanded Polystyrene'''
    def __init__(self):
        self.thermal_conductivity = 0.034
        self.specific_heat_capacity = 1300
        self.density = 52.3
        self.thermal_diffusivity = self.thermal_conductivity/(self.specific_heat_capacity*self.density)
