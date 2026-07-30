//+------------------------------------------------------------------+
//| Observatory.mq5                                                  |
//| EOS Binary Observatory                                           |
//+------------------------------------------------------------------+
#property strict
#property version "3.00"

#include "../Include/EventBase.mqh"
#include "../Include/EventTypes.mqh"
#include "../Include/Events.mqh"
#include "../Include/SocketClient.mqh"

input string InpSymbol = "EURUSD";

SocketClient g_socket;

string g_symbol;
ulong  g_counter = 0;

//---------------------------------------------------------------

void CopyString(char &dest[], string src)
{
   ArrayInitialize(dest, 0);
   StringToCharArray(src, dest, 0, ArraySize(dest));
}

//---------------------------------------------------------------

int OnInit()
{
   g_symbol = InpSymbol;

   if(!g_socket.Connect("127.0.0.1",5555))
   {
      Print("Unable to connect.");
      return INIT_FAILED;
   }

   Print("Connected.");

   return INIT_SUCCEEDED;
}

//---------------------------------------------------------------

void OnTick()
{
   MqlTick tick;

   if(!SymbolInfoTick(g_symbol,tick))
      return;

   TickObserved ev;

   ZeroMemory(ev);

   //============================================================
   // Metadata
   //============================================================

   CopyString(ev.meta.event_id,
      StringFormat("%s-%I64u",g_symbol,g_counter));

   ev.meta.domain               = DOMAIN_MARKET;
   ev.meta.event_type           = EV_TICK_OBSERVED;

   ev.meta.schema_version_major = 1;
   ev.meta.schema_version_minor = 0;

   ulong now=(ulong)GetTickCount64();

   ev.meta.exchange_time_ms = (ulong)tick.time_msc;
   ev.meta.local_time_ms    = now;
   ev.meta.monotonic_counter= g_counter;

   CopyString(ev.meta.producer,"MT5_Observer");
   CopyString(ev.meta.symbol,g_symbol);

   //============================================================
   // Payload
   //============================================================

   ev.bid          = tick.bid;
   ev.ask          = tick.ask;
   ev.last         = tick.last;
   ev.volume_real  = tick.volume_real;
   ev.volume_tick  = tick.volume;
   ev.flags        = tick.flags;

   g_socket.SendStruct(ev);

   g_counter++;
}

//---------------------------------------------------------------

void OnDeinit(const int reason)
{
   g_socket.Disconnect();

   Print("Ticks sent: ",g_counter);
}
