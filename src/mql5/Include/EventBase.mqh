//+------------------------------------------------------------------+
//| EventBase.mqh - The Immutable Envelope                          |
//+------------------------------------------------------------------+

#define MAX_EVENT_ID_LEN 64
#define MAX_SYMBOL_LEN 12
#define MAX_PRODUCER_LEN 32
#define MAX_ALGO_LEN 32
#define MAX_VERSION_LEN 16

struct EventMetadata {
    //--- Identification ---
    char   event_id[MAX_EVENT_ID_LEN];      
    ushort event_type;                      
    ushort domain;                          
    ushort schema_version_major;            
    ushort schema_version_minor;            
    
    //--- Timestamps ---
    ulong  exchange_time_ms;                
    ulong  local_time_ms;                   
    ulong  monotonic_counter;               
    
    //--- Source ---
    char   producer[MAX_PRODUCER_LEN];      
    char   session_id[MAX_EVENT_ID_LEN];    
    char   symbol[MAX_SYMBOL_LEN];          
    
    //--- Lineage ---
    char   parent_id_1[MAX_EVENT_ID_LEN];   
    char   parent_id_2[MAX_EVENT_ID_LEN];   
    char   algorithm[MAX_ALGO_LEN];         
    char   algo_version[MAX_VERSION_LEN];   
    
    //--- Integrity ---
    uint   checksum;                        
};
