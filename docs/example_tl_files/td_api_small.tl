authenticationCodeTypeCall length:int32 = AuthenticationCodeType;
temporaryPasswordState has_password:Bool valid_for:int32 = TemporaryPasswordState;
ok = Ok;

---functions---

getAuthorizationState = AuthorizationState;
setTdlibParameters parameters:tdlibParameters = Ok;
setAuthenticationPhoneNumber phone_number:string settings:phoneNumberAuthenticationSettings = Ok;
