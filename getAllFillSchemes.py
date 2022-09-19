import pytimber
import datetime
ldb = pytimber.LoggingDB(source="nxcals")

data = ldb.get("LHC.STATS:LHC:INJECTION_SCHEME", "2022-03-08 16:09:08", "2022-09-19 08:00:00", unixtime = True)

for i in range(len(data['LHC.STATS:LHC:INJECTION_SCHEME'][0])) :
    print(datetime.datetime.utcfromtimestamp(data['LHC.STATS:LHC:INJECTION_SCHEME'][0][i]), data['LHC.STATS:LHC:INJECTION_SCHEME'][1][i])

