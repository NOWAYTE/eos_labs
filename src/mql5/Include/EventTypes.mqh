//+------------------------------------------------------------------+
//| EventTypes.mqh - Core Enums and Type Definitions                 |
//| Complies with Event Schema v1.0.0                                |
//+------------------------------------------------------------------+

//--- Event Domains ---
enum EOS_EVENT_DOMAIN
{
   DOMAIN_MARKET      = 0,
   DOMAIN_DECISION    = 1,
   DOMAIN_EXECUTION   = 2,
   DOMAIN_PORTFOLIO   = 3,
   DOMAIN_EXPERIMENT  = 4
};

//--- Market Events ---
enum EOS_MARKET_EVENT
{
   EV_TICK_OBSERVED            = 0,
   EV_QUOTE_OBSERVED           = 1,
   EV_BAR_CLOSED               = 2
};

//--- Decision Events ---
enum EOS_DECISION_EVENT
{
   EV_MICROSTRUCTURE_ESTIMATED = 0,
   EV_ECONOMICS_EVALUATED      = 1,
   EV_REGIME_CLASSIFIED        = 2
};

//--- Execution Events ---
enum EOS_EXECUTION_EVENT
{
   EV_ORDER_REQUESTED = 0,
   EV_ORDER_ACCEPTED  = 1,
   EV_ORDER_FILLED    = 2,
   EV_ORDER_REJECTED  = 3
};

//--- Outcomes ---
enum EOS_DECISION_OUTCOME
{
   DEC_APPROVED = 0,
   DEC_REJECTED = 1,
   DEC_DEFER    = 2
};

//--- Order Types ---
enum EOS_ORDER_TYPE
{
   EOS_ORDER_MARKET = 0,
   EOS_ORDER_LIMIT  = 1,
   EOS_ORDER_STOP   = 2
};

//--- Order Sides ---
enum EOS_ORDER_SIDE
{
   EOS_SIDE_BUY  = 0,
   EOS_SIDE_SELL = 1
};
