from django import forms


class RBCDetectForm(forms.Form):
    param1 = forms.DecimalField(label="param1",max_value=255,min_value=0,decimal_places=2)
    param2 = forms.DecimalField(label="param2",max_value=255,min_value=0,decimal_places=2)
    minDist = forms.IntegerField(label="minDist",min_value=1)
    minRad = forms.IntegerField(label="minRad",min_value=1)
    maxRad = forms.IntegerField(label="maxRad",min_value=1)

