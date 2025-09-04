USE [id_banco]
GO 

/****** Object:  UserDefinedFunction [SCHEMA].[fn_UTMtoLatLon]    Script Date: 29/08/2025 15:24:50 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- Autor: Matheus Aviz
-- Função de reprojeção baseada na equação de Kruger - Versão Final - com Calibração de Precisão 0,3cm a 2,5m

CREATE FUNCTION [SCHEMA].[fn_UTMtoLatLon]
(
    @x FLOAT,
    @y FLOAT,
    @zone INT,
    @southHem BIT
)
RETURNS TABLE
AS
RETURN
(
    WITH consts AS (
        SELECT
            6378137.0 AS a,
            1.0/298.257222101 AS f,
            0.9996 AS k0,

            -- Fatores de compensação para a Zona 23
            CAST(-0.00000660005 AS FLOAT) AS Lat_Correction_Z23,
            CAST(0.0000000123 AS FLOAT) AS Lon_Correction_Z23,

            -- Fatores de compensação para a Zona 22
            CAST(-0.00007341 AS FLOAT) AS Lat_Correction_Z22,
            CAST(0.0000004662 AS FLOAT) AS Lon_Correction_Z22

    ),
    vars AS (
        SELECT *, (POWER(a, 2) - POWER(a * (1.0 - f), 2)) / POWER(a, 2) AS e2, (POWER(a, 2) - POWER(a * (1.0 - f), 2)) / POWER(a * (1.0 - f), 2) AS ep2 FROM consts
    ),
    calcs AS (
        SELECT *, @x - 500000.0 AS x, CASE WHEN @southHem = 1 THEN @y - 10000000.0 ELSE @y END AS y, CAST((@zone * 6) - 183 AS FLOAT) AS lon0_deg FROM vars
    ),
    M AS ( SELECT *, y / k0 AS M FROM calcs ),
    mu AS ( SELECT *, M / (a * (1.0 - e2/4.0 - 3*POWER(e2,2)/64.0 - 5*POWER(e2,3)/256.0)) AS mu FROM M ),
    e1 AS ( SELECT *, (1.0 - SQRT(1.0-e2)) / (1.0 + SQRT(1.0-e2)) AS e1 FROM mu ),
    phi1 AS (
        SELECT *, mu + (3.0*e1/2.0 - 27.0*POWER(e1,3)/32.0) * SIN(2.0*mu) + (21.0*POWER(e1,2)/16.0 - 55.0*POWER(e1,4)/32.0) * SIN(4.0*mu) + (151.0*POWER(e1,3)/96.0) * SIN(6.0*mu) + (1097.0*POWER(e1,4)/512.0) * SIN(8.0*mu) AS phi1_rad FROM e1
    ),
    final_terms AS (
        SELECT *, a / SQRT(1.0 - e2 * POWER(SIN(phi1_rad), 2)) AS N1, TAN(phi1_rad) AS T1, ep2 * POWER(COS(phi1_rad), 2) AS C1, a * (1.0 - e2) / POWER(1.0 - e2 * POWER(SIN(phi1_rad), 2), 1.5) AS R1 FROM phi1
    ),
    uncompensated_results AS (
        SELECT
            (phi1_rad - (T1 * POWER(x, 2)) / (2.0 * R1 * N1 * k0*k0) + (T1 * (5.0 + 3.0*T1*T1 + 10.0*C1 - 4.0*C1*C1 - 9.0*ep2) * POWER(x, 4)) / (24.0 * R1 * POWER(N1,3) * POWER(k0,4)) - (T1 * (61.0 + 90.0*T1*T1 + 298.0*C1 + 45.0*POWER(T1,4) - 252.0*ep2 - 3.0*C1*C1) * POWER(x, 6)) / (720.0 * R1 * POWER(N1,5) * POWER(k0,6))) * (180.0 / PI()) AS Latitude_Unc,
            (lon0_deg + ((x / (N1 * COS(phi1_rad) * k0)) - ((1.0 + 2.0*T1*T1 + C1) * POWER(x, 3)) / (6.0 * POWER(N1,3) * COS(phi1_rad) * POWER(k0,3)) + ((5.0 - 2.0*C1 + 28.0*T1*T1 - 3.0*C1*C1 + 8.0*ep2 + 24.0*POWER(T1,4)) * POWER(x, 5)) / (120.0 * POWER(N1,5) * COS(phi1_rad) * POWER(k0,5))) * (180.0 / PI())) AS Longitude_Unc,
            *
        FROM final_terms
    )
    -- CAMADA FINAL DE COMPENSAÇÃO PARA MÚLTIPLAS ZONAS
    SELECT
        CASE 
            WHEN @zone = 23 THEN ur.Latitude_Unc + ur.Lat_Correction_Z23
            WHEN @zone = 22 THEN ur.Latitude_Unc + ur.Lat_Correction_Z22
            ELSE ur.Latitude_Unc
        END AS Latitude,
        
        CASE 
            WHEN @zone = 23 THEN ur.Longitude_Unc + ur.Lon_Correction_Z23
            WHEN @zone = 22 THEN ur.Longitude_Unc + ur.Lon_Correction_Z22
            ELSE ur.Longitude_Unc
        END AS Longitude
    FROM uncompensated_results ur
);
GO


