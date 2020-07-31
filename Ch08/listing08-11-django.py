from django.db import models
from django.db.models.functions.datetime import TruncDate

@TruncDate.register_lookup
class DateExact(models.Lookup):
    lookup_name = 'exact'

    def as_sql(self, compiler, connection):
        # self.lhs (left-hand-side of the comparison) is always TruncDate, we want its argument
        underlying_dt = self.lhs.lhs
        # Instead, we want to wrap the rhs with TruncDate
        other_date = TruncDate(self.rhs)
        # Compile both sides
        lhs, lhs_params = compiler.compile(underlying_dt)
        rhs, rhs_params = compiler.compile(other_date)
        params = lhs_params + rhs_params + lhs_params + rhs_params
        # Return ((lhs >= rhs) AND (lhs < rhs+1)) - compatible with postgresql only!
        return '%s >= %s AND %s < (%s + 1)' % (lhs, rhs, lhs, rhs), params

