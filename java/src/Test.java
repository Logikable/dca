import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

/**
 * Created by Sean on 7/28/2017.
 */
public class Test {
    public static void main(String[] args) {
        DateTimeFormatter format = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        LocalDateTime time = LocalDate.parse("2017-07-28", format).atStartOfDay();
        LocalDateTime now = LocalDateTime.from(Instant.ofEpochSecond(1501259651).atZone(ZoneId.systemDefault()));
        System.out.println(time.plusDays(1).format(format));
    }
}
