//+------------------------------------------------------------------+
//| Events.mqh - Concrete Event Payloads                            |
//+------------------------------------------------------------------+


#include "EventBase.mqh"
#include "EventTypes.mqh"
// --- Domain 1: Market ---
struct TickObserved {
    EventMetadata meta;
    double bid;
    double ask;
    double last;
    double volume_real;
    ulong  volume_tick;
    uint   flags;
};

struct BarClosed {
    EventMetadata meta;
    int    interval_sec;
    double open;
    double high;
    double low;
    double close;
    ulong  tick_volume;
    double spread_avg;
};

// --- Domain 2: Decision ---
struct MicrostructureEstimated {
    EventMetadata meta;
    double tick_to_vol_ratio;
    double spread_bps;
    double book_imbalance;
    double toxicity_score;
    int    queue_position_est;
    double confidence_overall;
    double confidence_queue;
};

struct EconomicsEvaluated {
    EventMetadata meta;
    ushort outcome;                      
    char   reason[64];                   
    double nevw;
    double ppe;
    double execution_budget_bps;
    double edge_uncertainty;
    double cost_uncertainty;
};

// --- Domain 3: Execution ---
struct OrderRequested {
    EventMetadata meta;
    char   order_id_local[MAX_EVENT_ID_LEN];
    ushort side;                         
    ushort type;                         
    double price;
    double volume;
    double budget_constraint_bps;
};

struct OrderFilled {
    EventMetadata meta;
    char   order_id_local[MAX_EVENT_ID_LEN];
    ulong  mt5_ticket;
    double fill_price;
    double fill_volume;
    double commission_actual;
    double swap_actual;
    double realized_slippage;
};
