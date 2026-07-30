//+------------------------------------------------------------------+
//| SocketClient.mqh                                                 |
//| EOS Binary TCP Client                                            |
//+------------------------------------------------------------------+

class SocketClient
{
private:

   int m_socket;

public:

   SocketClient()
   {
      m_socket = INVALID_HANDLE;
   }

   ~SocketClient()
   {
      Disconnect();
   }

   //-----------------------------------------------------------------
   // Connect
   //-----------------------------------------------------------------

   bool Connect(string host="127.0.0.1", uint port=5555)
   {
      ResetLastError();

      m_socket = SocketCreate(SOCKET_DEFAULT);

      if(m_socket == INVALID_HANDLE)
      {
         Print("[Socket] SocketCreate failed. Error=", GetLastError());
         return false;
      }

      if(!SocketConnect(m_socket, host, port, 1000))
      {
         Print("[Socket] SocketConnect failed. Error=", GetLastError());

         SocketClose(m_socket);
         m_socket = INVALID_HANDLE;

         return false;
      }

      Print("[Socket] Connected to ", host, ":", port);

      return true;
   }

   //-----------------------------------------------------------------
   // Send raw bytes
   //-----------------------------------------------------------------

   bool SendBytes(const uchar &buffer[])
   {
      if(m_socket == INVALID_HANDLE)
         return false;

      uint size = (uint)ArraySize(buffer);

      if(size == 0)
         return false;

      int sent = SocketSend(
         m_socket,
         buffer,
         size
      );

      if(sent != (int)size)
      {
         Print(
            "[Socket] SocketSend failed. Error=",
            GetLastError(),
            " Sent=",
            sent,
            " Expected=",
            size
         );

         return false;
      }

      return true;
   }

   //-----------------------------------------------------------------
   // Send uint32 (little-endian)
   //-----------------------------------------------------------------

   bool SendUInt32(uint value)
   {
      uchar header[4];

      header[0] = (uchar)( value        & 0xFF);
      header[1] = (uchar)((value >> 8 ) & 0xFF);
      header[2] = (uchar)((value >> 16) & 0xFF);
      header[3] = (uchar)((value >> 24) & 0xFF);

      return SendBytes(header);
   }

   //-----------------------------------------------------------------
   // Send struct
   //-----------------------------------------------------------------

   template<typename T>
   bool SendStruct(T &event)
   {
      uint size = (uint)sizeof(event);

      uchar payload[];

      ArrayResize(payload, size);

      StructToCharArray(
         event,
         payload,
         0
      );

      if(!SendUInt32(size))
         return false;

      return SendBytes(payload);
   }

   //-----------------------------------------------------------------
   // Disconnect
   //-----------------------------------------------------------------

   void Disconnect()
   {
      if(m_socket != INVALID_HANDLE)
      {
         SocketClose(m_socket);
         m_socket = INVALID_HANDLE;
      }
   }

};
