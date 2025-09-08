﻿using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Org.BouncyCastle.Pqc.Crypto.Falcon;
using Org.BouncyCastle.Security;
using System.Globalization;

namespace FalconC_sharp_Grafica
{
    class Program
    {
        static void Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

            var mensajeCorto = "Mensaje pequeño para Falcon";
            var mensajeLargo = new string('A', 10000); // 10.000 caracteres

            var versiones = new[] { "Falcon512", "Falcon1024" };
            var resultadosGlobales = new List<ResultadoGlobal>();

            foreach (var version in versiones)
            {
                Console.WriteLine($"\n--- Pruebas para {version} ---");

                var random = new SecureRandom();
                var parametros = version switch
                {
                    "Falcon1024" => new FalconKeyGenerationParameters(random, FalconParameters.falcon_1024),
                    _ => new FalconKeyGenerationParameters(random, FalconParameters.falcon_512),
                };

                resultadosGlobales.Add(EjecutarPruebas(mensajeCorto, parametros, "pequeño", version));
                resultadosGlobales.Add(EjecutarPruebas(mensajeLargo, parametros, "grande", version));
            }

            using (var writer = new StreamWriter("Falcon_Global_Stats.csv"))
            {
                writer.WriteLine("Versión,Tamaño Mensaje,Generación Claves,Firma,Verificación");
                foreach (var r in resultadosGlobales)
                {
                    writer.WriteLine($"{r.Version},{r.TamañoMensaje}," +
                        $"{r.PromedioGeneracion:F4} ms (+-{r.DesviacionGeneracion:F4})," +
                        $"{r.PromedioFirma:F4} ms (+-{r.DesviacionFirma:F4})," +
                        $"{r.PromedioVerificacion:F4} ms (+-{r.DesviacionVerificacion:F4})");
                }
            }

            Console.WriteLine("\n✅ Resultados globales exportados a 'Falcon_Global_Stats.csv'");
        }

        static ResultadoGlobal EjecutarPruebas(string mensaje, FalconKeyGenerationParameters parametros, string tamaño, string version)
        {
            var tiemposGen = new List<double>();
            var tiemposFirma = new List<double>();
            var tiemposVerif = new List<double>();
            int iteraciones = 1000;
            string archivo = $"{version}_{tamaño}_performance.csv";

            using var writer = new StreamWriter(archivo);
            writer.WriteLine("Iteración,Falcon Version,Tamaño Mensaje,Tiempo Generación Claves,Tiempo Firma,Tiempo Verificación,Tiempo Total");

            for (int i = 0; i < iteraciones; i++)
            {
                var sw = Stopwatch.StartNew();
                var keyGen = new FalconKeyPairGenerator();
                keyGen.Init(parametros);
                var keyPair = keyGen.GenerateKeyPair();
                sw.Stop();
                var tGen = sw.Elapsed.TotalMilliseconds;
                tiemposGen.Add(tGen);

                var priv = (FalconPrivateKeyParameters)keyPair.Private;
                var pub = (FalconPublicKeyParameters)keyPair.Public;

                var signer = new FalconSigner();
                signer.Init(true, priv);
                sw.Restart();
                var sig = signer.GenerateSignature(System.Text.Encoding.UTF8.GetBytes(mensaje));
                sw.Stop();
                var tFirma = sw.Elapsed.TotalMilliseconds;
                tiemposFirma.Add(tFirma);

                var verifier = new FalconSigner();
                verifier.Init(false, pub);
                sw.Restart();
                bool ok = verifier.VerifySignature(System.Text.Encoding.UTF8.GetBytes(mensaje), sig);
                sw.Stop();
                var tVerif = sw.Elapsed.TotalMilliseconds;
                tiemposVerif.Add(tVerif);

                if (!ok)
                {
                    Console.WriteLine($"❌ Firma no válida en iteración {i + 1}");
                    return null;
                }

                double total = tGen + tFirma + tVerif;
                writer.WriteLine($"{i + 1},{version},{tamaño},{tGen:F4},{tFirma:F4},{tVerif:F4},{total:F4}");
            }

            Console.WriteLine($"📄 Resultados exportados a '{archivo}'");

            var promGen = tiemposGen.Average();
            var promFirma = tiemposFirma.Average();
            var promVerif = tiemposVerif.Average();

            var desvGen = CalcularDesviacion(tiemposGen, promGen);
            var desvFirma = CalcularDesviacion(tiemposFirma, promFirma);
            var desvVerif = CalcularDesviacion(tiemposVerif, promVerif);

            Mostrar("Generación", tiemposGen);
            Mostrar("Firma", tiemposFirma);
            Mostrar("Verificación", tiemposVerif);

            return new ResultadoGlobal
            {
                Version = version,
                TamañoMensaje = tamaño,
                PromedioGeneracion = promGen,
                DesviacionGeneracion = desvGen,
                PromedioFirma = promFirma,
                DesviacionFirma = desvFirma,
                PromedioVerificacion = promVerif,
                DesviacionVerificacion = desvVerif
            };
        }

        static void Mostrar(string nombre, List<double> valores)
        {
            var prom = valores.Average();
            var desv = CalcularDesviacion(valores, prom);
            Console.WriteLine($"--- {nombre} ---");
            Console.WriteLine($"Media: {prom:F4} ms");
            Console.WriteLine($"Desviación estándar: {desv:F4} ms");
        }

        static double CalcularDesviacion(List<double> valores, double media)
        {
            return Math.Sqrt(valores.Average(v => Math.Pow(v - media, 2)));
        }
    }

    class ResultadoGlobal
    {
        public string Version { get; set; }
        public string TamañoMensaje { get; set; }
        public double PromedioGeneracion { get; set; }
        public double DesviacionGeneracion { get; set; }
        public double PromedioFirma { get; set; }
        public double DesviacionFirma { get; set; }
        public double PromedioVerificacion { get; set; }
        public double DesviacionVerificacion { get; set; }
    }
}
