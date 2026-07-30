//+------------------------------------------------------------------+
//| LayoutInspector.mq5                                              |
//| Prints the actual MQL5 struct sizes                              |
//+------------------------------------------------------------------+
#property strict

#include "../Include/EventTypes.mqh"
#include "../Include/EventBase.mqh"
#include "../Include/Events.mqh"

int OnInit()
{
   Print("========== EOS Layout Inspector ==========");

   Print("sizeof(char) = ", sizeof(char));
   Print("sizeof(ushort) = ", sizeof(ushort));
   Print("sizeof(uint) = ", sizeof(uint));
   Print("sizeof(ulong) = ", sizeof(ulong));
   Print("sizeof(double) = ", sizeof(double));

   Print("------------------------------------------");

   Print("sizeof(EventMetadata) = ", sizeof(EventMetadata));
   Print("sizeof(TickObserved) = ", sizeof(TickObserved));
   Print("sizeof(BarClosed) = ", sizeof(BarClosed));

   Print("------------------------------------------");

   Print("MAX_EVENT_ID_LEN = ", MAX_EVENT_ID_LEN);
   Print("MAX_SYMBOL_LEN   = ", MAX_SYMBOL_LEN);
   Print("MAX_PRODUCER_LEN = ", MAX_PRODUCER_LEN);
   Print("MAX_ALGO_LEN     = ", MAX_ALGO_LEN);
   Print("MAX_VERSION_LEN  = ", MAX_VERSION_LEN);

   Print("==========================================");

   return INIT_SUCCEEDED;
}

void OnTick()
{
}

void OnDeinit(const int reason)
{
}
