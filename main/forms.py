from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", widget=forms.TextInput(attrs={'autofocus': 'true'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class CSVReportUploadForm(forms.Form):
    file = forms.FileField(label="Quiz Report (In CSV)", widget=forms.FileInput(attrs={'accept': '.csv'}))
