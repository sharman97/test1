from django.db import models

# Create your models here.
class RBCDetectParams(models.Model):
    param1 = models.FloatField()
    param2 = models.FloatField()# max_digits=3,decimal_places=2)
    minDist = models.IntegerField( )
    minRad = models.IntegerField()
    maxRad = models.IntegerField()
    def asdict(self):
        return {"param1": self.param1,
                  "param2": self.param2 ,
                  "minDist":self.minDist ,
                  "minRad":self.minRad ,
                  "maxRad": self.maxRad
                }
    def updatedict(self,params):
        self.param1 = params["param1"]
        self.param2 = params["param2"]

        self.minDist = params["minDist"]
        self.minRad = params["minRad"]
        self.maxRad = params["maxRad"]
        