#include <string>
#include "G4ios.hh"

#include "WCSimEnumerations.hh"

std::string WCSimEnumerations::EnumAsString(DigitizerType_t d)
{
  switch(d) {
  case (kDigitizerSKI) :
    return "SKI";
    break;
  default:
    return "";
    break;
  }
  return "";
}

std::string WCSimEnumerations::EnumAsString(TriggerType_t t)
{
  switch(t) {
  case (kTriggerNDigits) :
    return "NDigits";
    break;
  case (kTriggerLocalNHits) :
    return "Local_NHits";
    break;
  case (kTriggerNDigitsTest) :
    return "NDigits_TEST";
    break;
  case (kTriggerITCRatio) :
    return "ITCRatio";
    break;
  case (kTriggerRegions) :
    return "Regions";
    break;
  case (kTriggerAnisotropy) :
    return "Anisotropy";
    break;
  case (kTriggerNoTrig) :
    return "NoTrigger";
    break;
  case (kTriggerFailure) :
    return "No_trigger_passed";
    break;
  case (kTriggerNoTrig) :
    return "NoTrigger";
    break;
  default:
    return "";
    break;
  }
  return "";
}

TriggerType_t WCSimEnumerations::TriggerTypeFromString(std::string s)
{
  for(int i = int(kTriggerUndefined)+1; i <= kTriggerFailure; i++) {
    if(s.compare(WCSimEnumerations::EnumAsString((TriggerType_t)i)) == 0) {
      return (TriggerType_t)i;
    }
  }
  G4cerr << "WCSimEnumerations::TriggerTypeFromString() Unknown string value " << s << G4endl;
  return kTriggerUndefined;
}
