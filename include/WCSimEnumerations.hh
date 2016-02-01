#ifndef WCSimEnumerations_h
#define WCSimEnumerations_h 1

#include <string>
#include <iostream>

typedef enum ETriggerType {
  kTriggerUndefined = -1,
  kTriggerNDigits,
  kTriggerNDigitsTest,
  kTriggerLocalNHits,
  kTriggerITCRatio,
  kTriggerRegions,
  kTriggerAnisotropy,
  kTriggerNoTrig,
  kTriggerFailure // this should always be the last entry (for looping)
} TriggerType_t;

typedef enum EDigitizerType {
  kDigitizerUndefined = -1,
  kDigitizerSKI
} DigitizerType_t;

class WCSimEnumerations
{
public:

  static std::string EnumAsString(DigitizerType_t d)
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

  static std::string EnumAsString(TriggerType_t t)
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
    default:
      return "";
      break;
    }
    return "";
  }

  static TriggerType_t TriggerTypeFromString(std::string s)
  {
    for(int i = int(kTriggerUndefined)+1; i <= kTriggerFailure; i++) {
      if(s.compare(WCSimEnumerations::EnumAsString((TriggerType_t)i)) == 0) {
	return (TriggerType_t)i;
      }
    }
    std::cerr << "WCSimEnumerations::TriggerTypeFromString() Unknown string value " << s << std::endl;
    return kTriggerUndefined;
  }

};

#endif
