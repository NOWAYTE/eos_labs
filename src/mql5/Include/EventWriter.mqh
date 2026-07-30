//+------------------------------------------------------------------+
//| EventWriter.mqh - High-performance Binary Logging               |
//+------------------------------------------------------------------+

#include "Events.mqh"

class EventWriter {
private:
    int    m_file_handle;
    string m_base_path;
    string m_current_symbol;
    string m_current_date;

    string GetFileName(string symbol, int date_int) {
        // Uses FILE_COMMON so it writes to:
        // Common/Files/EventStore/
        return StringFormat("EventStore\\%s_%d.evts", symbol, date_int);
    }

public:
    EventWriter() {
        m_file_handle = INVALID_HANDLE;
    }

    ~EventWriter() {
        if(m_file_handle != INVALID_HANDLE)
            FileClose(m_file_handle);
    }

    //--- Open daily file in the Common Files directory ---
    bool Open(string symbol) {
        MqlDateTime dt;
        TimeCurrent(dt);

        int date_int = dt.year * 10000 + dt.mon * 100 + dt.day;
        m_current_date = StringFormat("%04d%02d%02d", dt.year, dt.mon, dt.day);

        string filename = GetFileName(symbol, date_int);

        ResetLastError();

        m_file_handle = FileOpen(
            filename,
            FILE_READ | FILE_WRITE | FILE_BIN | FILE_COMMON,
            '\t',
            CP_ACP
        );

        if(m_file_handle == INVALID_HANDLE) {
            Print("[EventWriter] Failed to open: ", filename,
                  " Error: ", GetLastError());
            return false;
        }

        // Append to existing file
        FileSeek(m_file_handle, 0, SEEK_END);

        m_current_symbol = symbol;

        Print("[EventWriter] Opened: ", filename,
              " (Size: ", FileSize(m_file_handle), " bytes)");

        return true;
    }

    //--- Generic Write ---
    template<typename T>
    bool Write(T &event) {

        if(m_file_handle == INVALID_HANDLE)
            return false;

        long before = FileTell(m_file_handle);

        ResetLastError();

        bool ok = FileWriteStruct(m_file_handle, event);

        if(!ok) {
            Print("[EventWriter] FileWriteStruct failed. Error=",
                  GetLastError());
            return false;
        }

        long after = FileTell(m_file_handle);

        Print("[EventWriter] Bytes written = ", after - before);

        FileFlush(m_file_handle);

        return true;
    }
};
